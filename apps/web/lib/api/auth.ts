import { apiClient } from "@/lib/api-client";

export interface TermsAgreementItem {
  termsId: number;
  agreed: boolean;
}

export interface SignupCompleteRequest {
  agreements: TermsAgreementItem[];
}

export interface SignupCompleteResponse {
  userId: string;
  message: string;
  success: boolean;
}

export interface UserProfile {
  userId: string;
  email: string;
  displayName: string;
  profileImageUrl: string;
  provider: string;
  status: "PENDING" | "ACTIVE" | "INACTIVE" | "WITHDRAWN";
}

export const completeSignup = async (data: SignupCompleteRequest): Promise<SignupCompleteResponse> => {
  return apiClient<SignupCompleteResponse>("/api/v1/auth/signup/complete", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const getCurrentUser = async (): Promise<UserProfile> => {
  return apiClient<UserProfile>("/api/v1/auth/me");
};
