"""
Integration tests for Unit of Work pattern
Tests transaction management, rollback, and ACID properties
"""
import pytest
import asyncio
from uuid import uuid4

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from database.unit_of_work import get_unit_of_work
from database.connection import init_db, close_db


@pytest.mark.asyncio
async def test_successful_transaction():
    """Test that successful operations commit atomically"""
    print("\n" + "=" * 70)
    print("TEST: Successful Transaction")
    print("=" * 70)
    
    test_email = f"test_{uuid4().hex[:8]}@example.com"
    
    async with get_unit_of_work() as uow:
        # Create customer
        customer = await uow.customers.create(
            email=test_email,
            name="Test User",
            plan="free",
            extra_metadata={}
        )
        print(f"✓ Customer created: {customer.email}")
        
        # Create conversation
        conversation = await uow.conversations.create_with_customer(
            customer_id=customer.id,
            status="active"
        )
        print(f"✓ Conversation created: {conversation.id}")
        
        # Create message
        message = await uow.messages.create_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello!"
        )
        print(f"✓ Message created: {message.content}")
        
        # Transaction commits here
    
    # Verify data persisted
    async with get_unit_of_work() as uow:
        # Check customer exists
        found_customer = await uow.customers.get_by_email(test_email)
        assert found_customer is not None
        assert found_customer.email == test_email
        print(f"✓ Customer persisted in database")
        
        # Check conversation exists
        conversations = await uow.conversations.get_by_customer(found_customer.id)
        assert len(conversations) == 1
        print(f"✓ Conversation persisted in database")
        
        # Cleanup
        await uow.conversations.delete(conversation.id)
        await uow.customers.delete(found_customer.id)
    
    print("✓ Test passed: Transaction committed successfully")


@pytest.mark.asyncio
async def test_rollback_on_exception():
    """Test that exceptions trigger automatic rollback"""
    print("\n" + "=" * 70)
    print("TEST: Rollback on Exception")
    print("=" * 70)
    
    test_email = f"test_{uuid4().hex[:8]}@example.com"
    customer_id = None
    
    try:
        async with get_unit_of_work() as uow:
            # Create customer
            customer = await uow.customers.create(
                email=test_email,
                name="Test User",
                plan="free",
                extra_metadata={}
            )
            customer_id = customer.id
            print(f"✓ Customer created: {customer.email}")
            
            # Create conversation
            conversation = await uow.conversations.create_with_customer(
                customer_id=customer.id
            )
            print(f"✓ Conversation created: {conversation.id}")
            
            # Simulate error
            raise ValueError("Simulated error to test rollback")
            
    except ValueError as e:
        print(f"✓ Exception caught: {e}")
    
    # Verify data was rolled back
    async with get_unit_of_work() as uow:
        # Customer should NOT exist
        found_customer = await uow.customers.get_by_email(test_email)
        assert found_customer is None
        print(f"✓ Customer rolled back (not in database)")
        
        # If somehow it exists, clean up
        if customer_id:
            exists = await uow.customers.exists(customer_id)
            assert not exists
    
    print("✓ Test passed: Transaction rolled back successfully")


@pytest.mark.asyncio
async def test_multiple_operations_atomic():
    """Test that multiple operations are truly atomic"""
    print("\n" + "=" * 70)
    print("TEST: Atomic Multi-Step Operations")
    print("=" * 70)
    
    test_email = f"test_{uuid4().hex[:8]}@example.com"
    
    async with get_unit_of_work() as uow:
        # Step 1: Create customer
        customer = await uow.customers.create(
            email=test_email,
            name="Atomic Test User",
            plan="premium",
            extra_metadata={}
        )
        
        # Step 2: Create multiple conversations
        conv1 = await uow.conversations.create_with_customer(
            customer_id=customer.id,
            primary_intent="billing_upgrade"
        )
        conv2 = await uow.conversations.create_with_customer(
            customer_id=customer.id,
            primary_intent="technical_bug"
        )
        
        # Step 3: Create messages for both conversations
        msg1 = await uow.messages.create_message(
            conversation_id=conv1.id,
            role="user",
            content="I want to upgrade"
        )
        msg2 = await uow.messages.create_message(
            conversation_id=conv2.id,
            role="user",
            content="I found a bug"
        )
        
        print(f"✓ Created 1 customer, 2 conversations, 2 messages")
        
        # All commit together
    
    # Verify atomicity
    async with get_unit_of_work() as uow:
        customer = await uow.customers.get_by_email(test_email)
        assert customer is not None
        
        conversations = await uow.conversations.get_by_customer(customer.id)
        assert len(conversations) == 2
        
        messages1 = await uow.messages.get_by_conversation(conv1.id)
        messages2 = await uow.messages.get_by_conversation(conv2.id)
        assert len(messages1) == 1
        assert len(messages2) == 1
        
        print(f"✓ All operations committed atomically")
        
        # Cleanup
        await uow.conversations.delete(conv1.id)
        await uow.conversations.delete(conv2.id)
        await uow.customers.delete(customer.id)
    
    print("✓ Test passed: Multi-step operations are atomic")


@pytest.mark.asyncio
async def test_audit_trail():
    """Test that audit trail works with Unit of Work"""
    print("\n" + "=" * 70)
    print("TEST: Audit Trail Tracking")
    print("=" * 70)
    
    admin_user_id = uuid4()
    test_email = f"test_{uuid4().hex[:8]}@example.com"
    
    async with get_unit_of_work(current_user_id=admin_user_id) as uow:
        # Create with audit trail
        customer = await uow.customers.create(
            email=test_email,
            name="Audit Test User",
            plan="free",
            extra_metadata={},
            created_by=uow.current_user_id
        )
        
        assert customer.created_by == admin_user_id
        print(f"✓ Created with audit trail: created_by = {customer.created_by}")
        
        # Update with audit trail
        updated = await uow.customers.update(
            customer.id,
            name="Updated Name",
            updated_by=uow.current_user_id
        )
        
        assert updated.updated_by == admin_user_id
        print(f"✓ Updated with audit trail: updated_by = {updated.updated_by}")
        
        # Soft delete with audit trail
        deleted = await uow.customers.soft_delete_by_id(
            customer.id,
            deleted_by=uow.current_user_id
        )
        
        assert deleted.deleted_at is not None
        assert deleted.deleted_by == admin_user_id
        print(f"✓ Soft deleted with audit trail: deleted_by = {deleted.deleted_by}")
        
        # Cleanup (hard delete for test cleanup)
        await uow.customers.delete(customer.id)
    
    print("✓ Test passed: Audit trail works correctly")


@pytest.mark.asyncio
async def test_soft_delete_with_uow():
    """Test soft delete functionality through Unit of Work"""
    print("\n" + "=" * 70)
    print("TEST: Soft Delete")
    print("=" * 70)
    
    test_email = f"test_{uuid4().hex[:8]}@example.com"
    
    async with get_unit_of_work() as uow:
        # Create customer
        customer = await uow.customers.create(
            email=test_email,
            name="Soft Delete Test",
            plan="free",
            extra_metadata={}
        )
        customer_id = customer.id
        print(f"✓ Customer created: {customer.email}")
    
    # Soft delete
    async with get_unit_of_work() as uow:
        deleted = await uow.customers.soft_delete_by_id(customer_id)
        assert deleted.deleted_at is not None
        print(f"✓ Customer soft deleted")
    
    # Verify not returned in normal queries
    async with get_unit_of_work() as uow:
        found = await uow.customers.get_by_id(customer_id)
        assert found is None
        print(f"✓ Soft deleted customer excluded from normal queries")
        
        # But can be found with include_deleted=True
        found_deleted = await uow.customers.get_by_id(customer_id, include_deleted=True)
        assert found_deleted is not None
        assert found_deleted.deleted_at is not None
        print(f"✓ Soft deleted customer can be retrieved with include_deleted=True")
        
        # Restore
        restored = await uow.customers.restore(customer_id)
        assert restored.deleted_at is None
        print(f"✓ Customer restored")
        
        # Cleanup
        await uow.customers.delete(customer_id)
    
    print("✓ Test passed: Soft delete works correctly")


# Pytest fixtures
@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup database before tests"""
    await init_db()
    yield
    await close_db()


# Main function for direct execution
async def main():
    """Run all Unit of Work tests"""
    print("=" * 70)
    print("UNIT OF WORK TEST SUITE")
    print("=" * 70)
    
    try:
        await init_db()
        
        await test_successful_transaction()
        await test_rollback_on_exception()
        await test_multiple_operations_atomic()
        await test_audit_trail()
        await test_soft_delete_with_uow()
        
        print("\n" + "=" * 70)
        print("✓ ALL UNIT OF WORK TESTS PASSED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())