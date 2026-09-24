"use client";
import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";
import { getCachedDocuments } from "@/lib/offline";

export default function Home() {
  const { data: courses } = useSWR("/courses?limit=5", (p) => api(p));
  const { data: enr } = useSWR("/enrollments", (p) => api(p).catch(() => []));
  const [docs, setDocs] = useState < any[] > ([]);
  
  useEffect(() => { getCachedDocuments().then(d => d?.length && setDocs(d.slice(0, 3))); }, []);
  
  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">TechMusha</h1>
        <Link href="/login" className="btn-ghost text-sm">Sign in</Link>
      </header>

      {enr?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Continue learning</h2>
          <div className="space-y-2">
            {enr.slice(0, 3).map((e: any) => (
              <Link key={e.id} href={`/courses/${e.course_id}`} className="card flex justify-between items-center">
                <span className="truncate">{e.course_id.slice(0, 8)}…</span>
                <span className="chip">{Math.round(e.progress)}%</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-2">Recommended for you</h2>
        <div className="space-y-2">
          {(courses || []).map((c: any) => (
            <Link key={c.id} href={`/courses/${c.slug}`} className="card block">
              <div className="font-medium">{c.title}</div>
              <div className="text-xs text-neutral-400 mt-1">
                {c.category} · {c.level} · {c.price === 0 ? "Free" : `$${c.price}`}
              </div>
            </Link>
          ))}
        </div>
      </section>

      {docs.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Offline documents</h2>
          <div className="grid grid-cols-2 gap-2">
            {docs.map((d) => (
              <div key={d.id} className="card text-sm">{d.title}</div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}