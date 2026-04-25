export default function ProfileCard() {
  return (
    <div className="glass rounded-3xl p-8">
      <div className="flex items-center gap-4">
        <div className="h-14 w-14 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-400" />
        <div>
          <p className="text-lg font-semibold">Aarav Mehta</p>
          <p className="text-xs text-ink/60">Premium Analyst</p>
        </div>
      </div>
      <div className="mt-6 grid gap-4 text-sm text-ink/70">
        <div className="flex items-center justify-between">
          <span>Email</span>
          <span>aarav@truelens.ai</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Role</span>
          <span>User</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Plan</span>
          <span>Team</span>
        </div>
      </div>
    </div>
  );
}
