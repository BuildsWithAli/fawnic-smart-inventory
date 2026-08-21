import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { useAuth } from "../hooks/useAuth";

const ROLE_LABELS: Record<string, string> = {
  owner: "Owner",
  inventory_manager: "Inventory Manager",
  support: "Support",
};

export function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader title="Account" subtitle="Your FAWNIC profile" />
        <div className="grid grid-cols-1 gap-4 px-5 pb-5 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Username</p>
            <p className="mt-1 text-sm text-ink">{user?.username}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Email</p>
            <p className="mt-1 text-sm text-ink">{user?.email || "—"}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Full Name</p>
            <p className="mt-1 text-sm text-ink">
              {user ? `${user.first_name} ${user.last_name}`.trim() || "—" : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Role</p>
            <p className="mt-1">
              <Badge tone="accent">{user ? ROLE_LABELS[user.role] : "—"}</Badge>
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="About FAWNIC Smart Inventory" subtitle="System information" />
        <div className="grid grid-cols-1 gap-4 px-5 pb-5 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Application</p>
            <p className="mt-1 text-sm text-ink">FAWNIC Smart Inventory &amp; Order Management</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">AI Stock Assistant</p>
            <p className="mt-1 text-sm text-ink">
              Runs automatically on Kanban status changes. Configured server-side via environment variables
              (Claude primary, OpenAI fallback, Ollama optional for local development).
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
