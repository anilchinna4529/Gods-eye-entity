export function Card({
  title,
  children,
  right
}: {
  title: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-[var(--stroke)] bg-[var(--card)] shadow-[0_30px_80px_var(--shadow)] backdrop-blur">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--stroke)] px-5 py-3">
        <h2 className="text-sm font-semibold tracking-wide text-white/85">{title}</h2>
        {right ? <div>{right}</div> : null}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

