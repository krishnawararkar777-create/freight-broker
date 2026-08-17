export type RBACRole = 'Admin' | 'Claims Manager' | 'Claims Operator' | 'Senior Approver' | 'Finance';

export interface UserOrganization {
  id: string;
  name: string;
  type: 'broker' | 'carrier' | 'shipper';
  contingencyRate: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: RBACRole;
  organization: UserOrganization;
}
