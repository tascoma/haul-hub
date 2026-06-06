import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { OnboardingStatus } from "../types/onboarding";

interface State {
  status: OnboardingStatus | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useOnboardingStatus(): State {
  const { me } = useAuth();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!me) {
      setStatus(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await api.get<OnboardingStatus>("/me/onboarding-status");
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load onboarding status");
    } finally {
      setLoading(false);
    }
  }, [me]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { status, loading, error, refetch };
}
