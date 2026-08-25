import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { AlertCircle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import fawnicLogo from "../assets/FAWNIC_logo.png";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { extractErrorMessage } from "../api/client";

export function LoginPage() {
  const { user, login, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isAuthLoading && user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Invalid username or password."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <img src={fawnicLogo} alt="FAWNIC" className="h-12 w-12 rounded-lg object-cover" />
          <div>
            <h1 className="font-display text-2xl font-medium text-ink">FAWNIC</h1>
            <p className="text-sm text-muted">Smart Inventory &amp; Order Management</p>
          </div>
        </div>

        <div className="relative rounded-xl border border-border bg-surface p-6 shadow-sm before:absolute before:inset-x-6 before:top-0 before:h-px before:border-t before:border-dashed before:border-accent/40">
          <h2 className="mb-5 font-display text-lg font-medium text-ink">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Username"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {error && (
              <div className="flex items-center gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger">
                <AlertCircle size={15} className="shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" size="lg" isLoading={isSubmitting} className="mt-1 w-full">
              Sign in
            </Button>
          </form>
        </div>

        <p className="mt-5 text-center text-xs text-muted">
          Demo accounts: owner / manager / support — password pattern Role@12345
        </p>
      </div>
    </div>
  );
}
