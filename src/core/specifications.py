"""
Specification Pattern - Encapsulate business rules as composable objects

The Specification pattern allows business rules to be defined as objects that
can be combined using boolean logic (AND, OR, NOT). This makes rules testable,
reusable, and easy to understand.

Example:
    >>> from core.specifications import Specification
    >>> 
    >>> class IsActive(Specification[Conversation]):
    ...     def is_satisfied_by(self, conversation):
    ...         return conversation.status == "active"
    ...     
    ...     def reason_not_satisfied(self, conversation):
    ...         return f"Conversation is {conversation.status}, not active"
    >>> 
    >>> class HasMessages(Specification[Conversation]):
    ...     def is_satisfied_by(self, conversation):
    ...         return len(conversation.messages) > 0
    >>> 
    >>> # Combine specifications
    >>> can_resolve = IsActive().and_(HasMessages())
    >>> 
    >>> if can_resolve.is_satisfied_by(conversation):
    ...     resolve_conversation(conversation)
    >>> else:
    ...     error = can_resolve.reason_not_satisfied(conversation)

References:
    - Specification Pattern: https://en.wikipedia.org/wiki/Specification_pattern
    - Domain-Driven Design by Eric Evans
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

__all__ = [
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
]

T = TypeVar('T')


class Specification(ABC, Generic[T]):
    """
    Base class for specifications (business rules)
    
    A specification encapsulates a business rule as an object that can
    test whether a candidate satisfies the rule. Specifications can be
    combined using AND, OR, and NOT operations.
    
    Type Parameters:
        T: Type of object this specification tests
    
    Example:
        >>> class MinimumAgeSpec(Specification[User]):
        ...     def __init__(self, min_age: int):
        ...         self.min_age = min_age
        ...     
        ...     def is_satisfied_by(self, user: User) -> bool:
        ...         return user.age >= self.min_age
        ...     
        ...     def reason_not_satisfied(self, user: User) -> str:
        ...         return f"User age {user.age} is below minimum {self.min_age}"
        >>> 
        >>> spec = MinimumAgeSpec(18)
        >>> if spec.is_satisfied_by(user):
        ...     grant_access(user)
    """
    
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if candidate satisfies this specification
        
        Args:
            candidate: Object to test
        
        Returns:
            True if specification is satisfied, False otherwise
        """
        pass
    
    def reason_not_satisfied(self, candidate: T) -> str:
        """
        Get human-readable reason why specification is not satisfied
        
        Override this method to provide specific error messages that
        can be shown to users or logged.
        
        Args:
            candidate: Object that failed specification
        
        Returns:
            Explanation of why the specification failed
        
        Example:
            >>> spec = MinimumAgeSpec(18)
            >>> if not spec.is_satisfied_by(user):
            ...     print(spec.reason_not_satisfied(user))
            "User age 16 is below minimum 18"
        """
        return f"{self.__class__.__name__} not satisfied"
    
    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        """
        Combine with another specification using AND logic
        
        Creates a composite specification that is satisfied only when
        both this specification AND the other specification are satisfied.
        
        Args:
            other: Another specification to AND with this one
        
        Returns:
            Composite specification requiring both
        
        Example:
            >>> adult = MinimumAgeSpec(18)
            >>> verified = IsVerifiedSpec()
            >>> can_vote = adult.and_(verified)
            >>> 
            >>> if can_vote.is_satisfied_by(user):
            ...     allow_voting(user)
        """
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        """
        Combine with another specification using OR logic
        
        Creates a composite specification that is satisfied when
        either this specification OR the other specification is satisfied.
        
        Args:
            other: Another specification to OR with this one
        
        Returns:
            Composite specification requiring either
        
        Example:
            >>> is_admin = IsAdminSpec()
            >>> is_moderator = IsModeratorSpec()
            >>> can_moderate = is_admin.or_(is_moderator)
            >>> 
            >>> if can_moderate.is_satisfied_by(user):
            ...     show_moderation_tools(user)
        """
        return OrSpecification(self, other)
    
    def not_(self) -> 'Specification[T]':
        """
        Negate this specification
        
        Creates a specification that is satisfied when this
        specification is NOT satisfied.
        
        Returns:
            Negated specification
        
        Example:
            >>> is_banned = IsBannedSpec()
            >>> is_allowed = is_banned.not_()
            >>> 
            >>> if is_allowed.is_satisfied_by(user):
            ...     grant_access(user)
        """
        return NotSpecification(self)
    
    def __and__(self, other: 'Specification[T]') -> 'Specification[T]':
        """Allow using & operator: spec1 & spec2"""
        return self.and_(other)
    
    def __or__(self, other: 'Specification[T]') -> 'Specification[T]':
        """Allow using | operator: spec1 | spec2"""
        return self.or_(other)
    
    def __invert__(self) -> 'Specification[T]':
        """Allow using ~ operator: ~spec"""
        return self.not_()


class AndSpecification(Specification[T]):
    """
    Composite specification combining two specs with AND logic
    
    Satisfied only when BOTH specifications are satisfied.
    """
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize AND specification
        
        Args:
            left: First specification
            right: Second specification
        """
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if both specifications are satisfied"""
        return (
            self.left.is_satisfied_by(candidate) and
            self.right.is_satisfied_by(candidate)
        )
    
    def reason_not_satisfied(self, candidate: T) -> str:
        """
        Get combined failure reasons
        
        Returns reasons from both specs if both fail,
        or from whichever spec fails.
        """
        reasons = []
        
        if not self.left.is_satisfied_by(candidate):
            reasons.append(self.left.reason_not_satisfied(candidate))
        
        if not self.right.is_satisfied_by(candidate):
            reasons.append(self.right.reason_not_satisfied(candidate))
        
        return " AND ".join(reasons) if reasons else ""
    
    def __repr__(self) -> str:
        return f"({self.left} AND {self.right})"


class OrSpecification(Specification[T]):
    """
    Composite specification combining two specs with OR logic
    
    Satisfied when EITHER specification is satisfied.
    """
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize OR specification
        
        Args:
            left: First specification
            right: Second specification
        """
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if either specification is satisfied"""
        return (
            self.left.is_satisfied_by(candidate) or
            self.right.is_satisfied_by(candidate)
        )
    
    def reason_not_satisfied(self, candidate: T) -> str:
        """
        Get combined failure reasons
        
        For OR, we show both reasons since neither was satisfied.
        """
        left_reason = self.left.reason_not_satisfied(candidate)
        right_reason = self.right.reason_not_satisfied(candidate)
        return f"({left_reason}) OR ({right_reason})"
    
    def __repr__(self) -> str:
        return f"({self.left} OR {self.right})"


class NotSpecification(Specification[T]):
    """
    Specification that negates another specification
    
    Satisfied when the wrapped specification is NOT satisfied.
    """
    
    def __init__(self, spec: Specification[T]):
        """
        Initialize NOT specification
        
        Args:
            spec: Specification to negate
        """
        self.spec = spec
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if specification is not satisfied"""
        return not self.spec.is_satisfied_by(candidate)
    
    def reason_not_satisfied(self, candidate: T) -> str:
        """
        Get negation failure reason
        
        This means the underlying spec WAS satisfied when it shouldn't be.
        """
        return f"NOT ({self.spec.__class__.__name__})"
    
    def __repr__(self) -> str:
        return f"NOT ({self.spec})"


if __name__ == "__main__":
    # Self-test
    print("=" * 70)
    print("SPECIFICATION PATTERN - SELF TEST")
    print("=" * 70)
    
    # Test data class
    from dataclasses import dataclass
    
    @dataclass
    class TestEntity:
        """Test entity for specification testing"""
        value: int
        active: bool
    
    # Test specifications
    class IsPositive(Specification[TestEntity]):
        """Test spec: value must be positive"""
        def is_satisfied_by(self, entity: TestEntity) -> bool:
            return entity.value > 0
        
        def reason_not_satisfied(self, entity: TestEntity) -> str:
            return f"Value {entity.value} is not positive"
    
    class IsActive(Specification[TestEntity]):
        """Test spec: must be active"""
        def is_satisfied_by(self, entity: TestEntity) -> bool:
            return entity.active
        
        def reason_not_satisfied(self, entity: TestEntity) -> str:
            return "Entity is not active"
    
    # Test basic specification
    print("\n1. Testing basic specification...")
    spec = IsPositive()
    entity_pass = TestEntity(value=5, active=True)
    entity_fail = TestEntity(value=-5, active=True)
    
    assert spec.is_satisfied_by(entity_pass)
    assert not spec.is_satisfied_by(entity_fail)
    print(f"   ✓ Basic specification works")
    
    # Test AND combination
    print("\n2. Testing AND specification...")
    and_spec = IsPositive().and_(IsActive())
    
    entity1 = TestEntity(value=5, active=True)   # Both satisfied
    entity2 = TestEntity(value=-5, active=True)  # Only active
    entity3 = TestEntity(value=5, active=False)  # Only positive
    entity4 = TestEntity(value=-5, active=False) # Neither
    
    assert and_spec.is_satisfied_by(entity1)
    assert not and_spec.is_satisfied_by(entity2)
    assert not and_spec.is_satisfied_by(entity3)
    assert not and_spec.is_satisfied_by(entity4)
    print(f"   ✓ AND specification works")
    
    # Test OR combination
    print("\n3. Testing OR specification...")
    or_spec = IsPositive().or_(IsActive())
    
    assert or_spec.is_satisfied_by(entity1)  # Both
    assert or_spec.is_satisfied_by(entity2)  # Only active
    assert or_spec.is_satisfied_by(entity3)  # Only positive
    assert not or_spec.is_satisfied_by(entity4)  # Neither
    print(f"   ✓ OR specification works")
    
    # Test NOT
    print("\n4. Testing NOT specification...")
    not_spec = IsPositive().not_()
    
    assert not not_spec.is_satisfied_by(entity_pass)  # Positive -> NOT fails
    assert not_spec.is_satisfied_by(entity_fail)  # Negative -> NOT succeeds
    print(f"   ✓ NOT specification works")
    
    # Test complex combination
    print("\n5. Testing complex combination...")
    complex_spec = IsPositive().and_(IsActive()).or_(IsPositive().not_())
    # (positive AND active) OR (NOT positive)
    # Succeeds if: (value > 0 and active) or (value <= 0)
    
    assert complex_spec.is_satisfied_by(TestEntity(5, True))    # positive + active
    assert complex_spec.is_satisfied_by(TestEntity(-5, True))   # NOT positive
    assert complex_spec.is_satisfied_by(TestEntity(-5, False))  # NOT positive
    assert not complex_spec.is_satisfied_by(TestEntity(5, False))  # positive but not active
    print(f"   ✓ Complex specification works")
    
    # Test reason messages
    print("\n6. Testing reason messages...")
    reason = and_spec.reason_not_satisfied(entity4)
    assert "not positive" in reason.lower()
    assert "not active" in reason.lower()
    print(f"   ✓ Reason: {reason}")
    
    # Test operator overloading
    print("\n7. Testing operator overloading...")
    op_and = IsPositive() & IsActive()
    op_or = IsPositive() | IsActive()
    op_not = ~IsPositive()
    
    assert op_and.is_satisfied_by(entity1)
    assert op_or.is_satisfied_by(entity2)
    assert op_not.is_satisfied_by(entity_fail)
    print(f"   ✓ Operators work (&, |, ~)")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)