export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  department: string;
  permissions: string[];
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: UserProfile;
}

