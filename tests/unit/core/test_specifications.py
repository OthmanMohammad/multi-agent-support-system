"""
Unit tests for Specification pattern

Tests cover:
- Basic specification evaluation
- Specification combinators (AND, OR, NOT)
- Complex specification chains
- Reason messages
- Operator overloading
"""

import pytest
from dataclasses import dataclass

from src.core.specifications import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
)


# Test entity and specifications

@dataclass
class Entity:
    """Test entity for specification testing"""
    value: int
    active: bool
    name: str = "test"


class IsPositive(Specification[Entity]):
    """Test specification: value must be positive"""
    
    def is_satisfied_by(self, entity: Entity) -> bool:
        return entity.value > 0
    
    def reason_not_satisfied(self, entity: Entity) -> str:
        return f"Value {entity.value} is not positive"


class IsActive(Specification[Entity]):
    """Test specification: entity must be active"""
    
    def is_satisfied_by(self, entity: Entity) -> bool:
        return entity.active
    
    def reason_not_satisfied(self, entity: Entity) -> str:
        return "Entity is not active"


class HasName(Specification[Entity]):
    """Test specification: entity must have a name"""
    
    def __init__(self, required_name: str):
        self.required_name = required_name
    
    def is_satisfied_by(self, entity: Entity) -> bool:
        return entity.name == self.required_name
    
    def reason_not_satisfied(self, entity: Entity) -> str:
        return f"Name is '{entity.name}', expected '{self.required_name}'"


class TestBasicSpecification:
    """Test suite for basic Specification functionality"""
    
    def test_specification_satisfied(self):
        """Test specification returns True when satisfied"""
        spec = IsPositive()
        entity = Entity(value=5, active=True)
        
        assert spec.is_satisfied_by(entity) is True
    
    def test_specification_not_satisfied(self):
        """Test specification returns False when not satisfied"""
        spec = IsPositive()
        entity = Entity(value=-5, active=True)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_reason_message_on_failure(self):
        """Test reason_not_satisfied provides explanation"""
        spec = IsPositive()
        entity = Entity(value=-5, active=True)
        
        reason = spec.reason_not_satisfied(entity)
        
        assert "not positive" in reason.lower()
        assert "-5" in reason
    
    def test_default_reason_message(self):
        """Test default reason_not_satisfied uses class name"""
        class MinimalSpec(Specification[Entity]):
            def is_satisfied_by(self, entity):
                return False
        
        spec = MinimalSpec()
        entity = Entity(value=0, active=False)
        
        reason = spec.reason_not_satisfied(entity)
        
        assert "MinimalSpec" in reason
    
    def test_specification_with_parameters(self):
        """Test specification with initialization parameters"""
        spec = HasName("test")
        
        assert spec.is_satisfied_by(Entity(0, False, "test"))
        assert not spec.is_satisfied_by(Entity(0, False, "other"))


class TestAndSpecification:
    """Test suite for AND combinator"""
    
    def test_and_both_satisfied(self):
        """Test AND succeeds when both specifications satisfied"""
        spec = IsPositive().and_(IsActive())
        entity = Entity(value=5, active=True)
        
        assert spec.is_satisfied_by(entity) is True
    
    def test_and_first_not_satisfied(self):
        """Test AND fails when first specification fails"""
        spec = IsPositive().and_(IsActive())
        entity = Entity(value=-5, active=True)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_and_second_not_satisfied(self):
        """Test AND fails when second specification fails"""
        spec = IsPositive().and_(IsActive())
        entity = Entity(value=5, active=False)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_and_neither_satisfied(self):
        """Test AND fails when both specifications fail"""
        spec = IsPositive().and_(IsActive())
        entity = Entity(value=-5, active=False)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_and_reason_includes_both_failures(self):
        """Test AND reason includes both failed specs"""
        spec = IsPositive().and_(IsActive())
        entity = Entity(value=-5, active=False)
        
        reason = spec.reason_not_satisfied(entity)
        
        assert "not positive" in reason.lower()
        assert "not active" in reason.lower()
        assert " AND " in reason
    
    def test_and_reason_only_failed_spec(self):
        """Test AND reason only includes failed specification"""
        spec = IsPositive().and_(IsActive())
        entity = Entity(value=-5, active=True)
        
        reason = spec.reason_not_satisfied(entity)
        
        assert "not positive" in reason.lower()
        assert "not active" not in reason.lower()
    
    def test_and_chaining_multiple(self):
        """Test chaining multiple AND specifications"""
        spec = IsPositive().and_(IsActive()).and_(HasName("test"))
        
        assert spec.is_satisfied_by(Entity(5, True, "test"))
        assert not spec.is_satisfied_by(Entity(5, True, "other"))
        assert not spec.is_satisfied_by(Entity(-5, True, "test"))


class TestOrSpecification:
    """Test suite for OR combinator"""
    
    def test_or_both_satisfied(self):
        """Test OR succeeds when both specifications satisfied"""
        spec = IsPositive().or_(IsActive())
        entity = Entity(value=5, active=True)
        
        assert spec.is_satisfied_by(entity) is True
    
    def test_or_first_satisfied(self):
        """Test OR succeeds when only first specification satisfied"""
        spec = IsPositive().or_(IsActive())
        entity = Entity(value=5, active=False)
        
        assert spec.is_satisfied_by(entity) is True
    
    def test_or_second_satisfied(self):
        """Test OR succeeds when only second specification satisfied"""
        spec = IsPositive().or_(IsActive())
        entity = Entity(value=-5, active=True)
        
        assert spec.is_satisfied_by(entity) is True
    
    def test_or_neither_satisfied(self):
        """Test OR fails when both specifications fail"""
        spec = IsPositive().or_(IsActive())
        entity = Entity(value=-5, active=False)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_or_reason_includes_both(self):
        """Test OR reason includes both specs when both fail"""
        spec = IsPositive().or_(IsActive())
        entity = Entity(value=-5, active=False)
        
        reason = spec.reason_not_satisfied(entity)
        
        assert " OR " in reason
        assert "(" in reason  # Parentheses for clarity
    
    def test_or_short_circuits(self):
        """Test OR short-circuits (implementation detail)"""
        spec = IsPositive().or_(IsActive())
        
        # Should succeed on first check
        assert spec.is_satisfied_by(Entity(5, False))


class TestNotSpecification:
    """Test suite for NOT combinator"""
    
    def test_not_negates_true(self):
        """Test NOT returns False when specification is satisfied"""
        spec = IsPositive().not_()
        entity = Entity(value=5, active=True)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_not_negates_false(self):
        """Test NOT returns True when specification is not satisfied"""
        spec = IsPositive().not_()
        entity = Entity(value=-5, active=True)
        
        assert spec.is_satisfied_by(entity) is True
    
    def test_not_reason_message(self):
        """Test NOT provides reason message"""
        spec = IsPositive().not_()
        entity = Entity(value=5, active=True)
        
        reason = spec.reason_not_satisfied(entity)
        
        assert "NOT" in reason
    
    def test_double_negation(self):
        """Test double NOT cancels out"""
        spec = IsPositive().not_().not_()
        
        assert spec.is_satisfied_by(Entity(5, True))
        assert not spec.is_satisfied_by(Entity(-5, True))


class TestComplexSpecifications:
    """Test suite for complex specification combinations"""
    
    def test_and_or_combination(self):
        """Test combining AND and OR"""
        # (positive AND active) OR (NOT positive)
        spec = IsPositive().and_(IsActive()).or_(IsPositive().not_())
        
        assert spec.is_satisfied_by(Entity(5, True))    # positive + active
        assert spec.is_satisfied_by(Entity(-5, True))   # NOT positive
        assert spec.is_satisfied_by(Entity(-5, False))  # NOT positive
        assert not spec.is_satisfied_by(Entity(5, False))  # positive but not active
    
    def test_nested_and_or(self):
        """Test nested AND/OR specifications"""
        # (positive OR active) AND hasName
        spec = IsPositive().or_(IsActive()).and_(HasName("test"))
        
        assert spec.is_satisfied_by(Entity(5, False, "test"))
        assert spec.is_satisfied_by(Entity(-5, True, "test"))
        assert not spec.is_satisfied_by(Entity(-5, False, "test"))
        assert not spec.is_satisfied_by(Entity(5, True, "other"))
    
    def test_complex_business_rule(self):
        """Test complex business rule specification"""
        # Can process: (positive AND active) OR (NOT active AND hasName "special")
        can_process = (
            IsPositive().and_(IsActive())
            .or_(IsActive().not_().and_(HasName("special")))
        )
        
        # Normal processing: positive and active
        assert can_process.is_satisfied_by(Entity(5, True, "normal"))
        
        # Special processing: inactive with special name
        assert can_process.is_satisfied_by(Entity(-5, False, "special"))
        
        # Should fail
        assert not can_process.is_satisfied_by(Entity(-5, False, "normal"))
        assert not can_process.is_satisfied_by(Entity(-5, True, "normal"))


class TestOperatorOverloading:
    """Test suite for operator overloading (& | ~)"""
    
    def test_and_operator(self):
        """Test & operator for AND"""
        spec = IsPositive() & IsActive()
        
        assert spec.is_satisfied_by(Entity(5, True))
        assert not spec.is_satisfied_by(Entity(5, False))
    
    def test_or_operator(self):
        """Test | operator for OR"""
        spec = IsPositive() | IsActive()
        
        assert spec.is_satisfied_by(Entity(5, False))
        assert spec.is_satisfied_by(Entity(-5, True))
        assert not spec.is_satisfied_by(Entity(-5, False))
    
    def test_not_operator(self):
        """Test ~ operator for NOT"""
        spec = ~IsPositive()
        
        assert spec.is_satisfied_by(Entity(-5, True))
        assert not spec.is_satisfied_by(Entity(5, True))
    
    def test_complex_with_operators(self):
        """Test complex expression with operators"""
        spec = (IsPositive() & IsActive()) | ~HasName("blocked")
        
        assert spec.is_satisfied_by(Entity(5, True, "normal"))
        assert spec.is_satisfied_by(Entity(-5, False, "normal"))
        assert not spec.is_satisfied_by(Entity(-5, False, "blocked"))


class TestSpecificationRepr:
    """Test suite for specification string representations"""
    
    def test_and_repr(self):
        """Test AND specification repr"""
        spec = IsPositive().and_(IsActive())
        
        repr_str = repr(spec)
        
        assert "AND" in repr_str
    
    def test_or_repr(self):
        """Test OR specification repr"""
        spec = IsPositive().or_(IsActive())
        
        repr_str = repr(spec)
        
        assert "OR" in repr_str
    
    def test_not_repr(self):
        """Test NOT specification repr"""
        spec = IsPositive().not_()
        
        repr_str = repr(spec)
        
        assert "NOT" in repr_str


@pytest.mark.parametrize("value,active,expected", [
    (5, True, True),   # Both satisfied
    (5, False, True),  # Only positive
    (-5, True, True),  # Only active
    (-5, False, False),  # Neither
])
def test_or_specification_parametrized(value, active, expected):
    """Parametrized test for OR specification"""
    spec = IsPositive().or_(IsActive())
    entity = Entity(value=value, active=active)
    
    assert spec.is_satisfied_by(entity) == expected


@pytest.mark.parametrize("value,expected", [
    (1, True),
    (0, False),
    (-1, False),
    (100, True),
    (-100, False),
])
def test_positive_specification_parametrized(value, expected):
    """Parametrized test for IsPositive specification"""
    spec = IsPositive()
    entity = Entity(value=value, active=True)
    
    assert spec.is_satisfied_by(entity) == expected