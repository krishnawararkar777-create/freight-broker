import pytest
from app.models.domain_models import User
from app.core.rbac import check_role_permission, RBACRole, ROLE_HIERARCHY_LEVELS

def test_shipper_roles_enum_and_hierarchy():
    assert RBACRole.SHIPPER_ADMIN == 'Shipper Admin'
    assert RBACRole.LOGISTICS_DIRECTOR == 'Logistics Director'
    assert RBACRole.LOGISTICS_COORDINATOR == 'Logistics Coordinator'
    assert RBACRole.PLANT_MANAGER_INSPECTOR == 'Plant Manager / Inspector'
    assert RBACRole.SHIPPER_FINANCE == 'Shipper Finance'

    assert ROLE_HIERARCHY_LEVELS[RBACRole.SHIPPER_ADMIN] == 100
    assert ROLE_HIERARCHY_LEVELS[RBACRole.LOGISTICS_DIRECTOR] == 80
    assert ROLE_HIERARCHY_LEVELS[RBACRole.LOGISTICS_COORDINATOR] == 50
    assert ROLE_HIERARCHY_LEVELS[RBACRole.PLANT_MANAGER_INSPECTOR] == 40
    assert ROLE_HIERARCHY_LEVELS[RBACRole.SHIPPER_FINANCE] == 20

def test_shipper_director_and_admin_elevated_approval():
    director = User(
        id='usr-dir-001',
        organization_id='org-shipper-01',
        name='Diana Director',
        email='diana@shipper.com',
        role='Logistics Director'
    )
    admin = User(
        id='usr-adm-001',
        organization_id='org-shipper-01',
        name='Sam Admin',
        email='sam@shipper.com',
        role='Shipper Admin'
    )

    # Claim for ,500
    assert check_role_permission(user_role=director.role, required_role=RBACRole.LOGISTICS_DIRECTOR, claimed_amount=7500.00) is True
    assert check_role_permission(user_role=admin.role, required_role=RBACRole.LOGISTICS_DIRECTOR, claimed_amount=7500.00) is True

def test_shipper_non_director_roles_blocked_from_elevated_approval():
    coordinator = User(
        id='usr-coord-001',
        organization_id='org-shipper-01',
        name='Carl Coordinator',
        email='carl@shipper.com',
        role='Logistics Coordinator'
    )
    inspector = User(
        id='usr-insp-001',
        organization_id='org-shipper-01',
        name='Ian Inspector',
        email='ian@shipper.com',
        role='Plant Manager / Inspector'
    )
    finance = User(
        id='usr-fin-001',
        organization_id='org-shipper-01',
        name='Fiona Finance',
        email='fiona@shipper.com',
        role='Shipper Finance'
    )

    # Claim for ,500 should be rejected for non-directors
    assert check_role_permission(user_role=coordinator.role, required_role=RBACRole.LOGISTICS_DIRECTOR, claimed_amount=7500.00) is False
    assert check_role_permission(user_role=inspector.role, required_role=RBACRole.LOGISTICS_DIRECTOR, claimed_amount=7500.00) is False
    assert check_role_permission(user_role=finance.role, required_role=RBACRole.LOGISTICS_DIRECTOR, claimed_amount=7500.00) is False

def test_shipper_sub_threshold_permission_hierarchy():
    # Logistics Coordinator (level 50) can sign for Plant Inspector (level 40)
    assert check_role_permission(user_role='Logistics Coordinator', required_role=RBACRole.PLANT_MANAGER_INSPECTOR, claimed_amount=2000.00) is True
    # Plant Inspector (level 40) cannot sign for Logistics Coordinator (level 50)
    assert check_role_permission(user_role='Plant Manager / Inspector', required_role=RBACRole.LOGISTICS_COORDINATOR, claimed_amount=2000.00) is False
