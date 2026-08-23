from enum import Enum
from typing import Optional
from fastapi import HTTPException, status, Depends
from pydantic import BaseModel

class RBACRole(str, Enum):
    # Broker / 3PL Roles
    ADMIN = "Admin"
    CLAIMS_MANAGER = "Claims Manager"
    CLAIMS_OPERATOR = "Claims Operator"
    SENIOR_APPROVER = "Senior Approver"
    FINANCE = "Finance"

    # Enterprise Shipper Roles
    SHIPPER_ADMIN = "Shipper Admin"
    LOGISTICS_DIRECTOR = "Logistics Director"
    LOGISTICS_COORDINATOR = "Logistics Coordinator"
    PLANT_MANAGER_INSPECTOR = "Plant Manager / Inspector"
    SHIPPER_FINANCE = "Shipper Finance"

ROLE_HIERARCHY_LEVELS = {
    RBACRole.ADMIN: 100,
    RBACRole.SHIPPER_ADMIN: 100,
    RBACRole.SENIOR_APPROVER: 80,
    RBACRole.LOGISTICS_DIRECTOR: 80,
    RBACRole.CLAIMS_MANAGER: 60,
    RBACRole.LOGISTICS_COORDINATOR: 50,
    RBACRole.CLAIMS_OPERATOR: 40,
    RBACRole.PLANT_MANAGER_INSPECTOR: 40,
    RBACRole.FINANCE: 20,
    RBACRole.SHIPPER_FINANCE: 20
}

ELEVATED_THRESHOLD_USD = 5000.00
ELEVATED_APPROVAL_ROLES = (
    RBACRole.ADMIN,
    RBACRole.SENIOR_APPROVER,
    RBACRole.SHIPPER_ADMIN,
    RBACRole.LOGISTICS_DIRECTOR
)

def check_role_permission(
    user_role: str,
    required_role: RBACRole,
    claimed_amount: Optional[float] = None
) -> bool:
    """
    Check if user's role has sufficient permission level.
    If claimed_amount >= ELEVATED_THRESHOLD_USD ($5,000), requires SENIOR_APPROVER, LOGISTICS_DIRECTOR, or ADMIN.
    """
    user_enum = RBACRole(user_role) if user_role in RBACRole._value2member_map_ else None
    if not user_enum:
        return False

    # Elevated threshold check ($5,000+)
    if claimed_amount is not None and claimed_amount >= ELEVATED_THRESHOLD_USD:
        return user_enum in ELEVATED_APPROVAL_ROLES

    user_level = ROLE_HIERARCHY_LEVELS.get(user_enum, 0)
    required_level = ROLE_HIERARCHY_LEVELS.get(required_role, 0)
    return user_level >= required_level

def require_roles(*allowed_roles: RBACRole):
    """FastAPI dependency wrapper for RBAC role authorization."""
    def role_checker(user_role: str):
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{user_role}' lacks required permissions."
            )
        return True
    return role_checker
