export type RBACRole =
  | 'Admin'
  | 'Claims Manager'
  | 'Claims Operator'
  | 'Senior Approver'
  | 'Finance'
  | 'Plant Manager / Inspector'
  | 'Logistics Coordinator'
  | 'Logistics Director'
  | 'Shipper Finance'
  | 'Shipper Admin';

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

