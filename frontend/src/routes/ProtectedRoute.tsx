import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Loader2 } from "lucide-react";

export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg">
        <Loader2 className="animate-spin text-accent" size={28} />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}

export function OwnerOnlyRoute() {
  const { isOwner } = useAuth();

  if (!isOwner) return <Navigate to="/" replace />;

  return <Outlet />;
}
