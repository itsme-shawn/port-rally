import { apiClient } from "@/lib/api-client";

export interface TermsResponse {
  termsId: number;
  termsType: string;
  title: string;
  content: string;
  isRequired: boolean;
  displayOrder: number;
}

export const getActiveTerms = async (): Promise<TermsResponse[]> => {
  return apiClient<TermsResponse[]>("/api/v1/terms");
};
