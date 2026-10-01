import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { api } from "../api/endpoints";
import type { LessonPreview } from "../api/types";
import { ErrorNote, Loading, PageHeader } from "../ui";
import { LessonView } from "./LessonView";

export function LessonPreviewPage() {
  const { previewId } = useParams<{ previewId: string }>();
  const [preview, setPreview] = useState<LessonPreview | null>(null);
  const [choices, setChoices] = useState<{ id: string; title: string }[]>([]);
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let alive = true;
    setPreview(null); setFailed(false);
    if (!previewId) return;
    Promise.all([api.lessonPreview(previewId), api.lessonPreviews()]).then(([value, index]) => {
      if (alive) { setPreview(value); setChoices(index.lessons); }
    }).catch(() => { if (alive) setFailed(true); });
    return () => { alive = false; };
  }, [previewId, retry]);
  return <div className="mx-auto max-w-3xl">
    <Link to="/learn" className="mb-5 inline-flex items-center gap-2 text-sm text-forest-700"><ArrowLeft size={14} /> Learn</Link>
    <p className="mb-3 text-xs font-medium uppercase tracking-wide text-clay-600">Lesson preview · awaiting review</p>
    <nav aria-label="Lesson previews" className="mb-6 flex flex-wrap gap-2">{choices.map(choice => <Link key={choice.id}
      to={`/learn-preview/${choice.id}`} aria-current={choice.id === previewId ? "page" : undefined}
      className={`border px-3 py-2 text-xs ${choice.id === previewId ? "border-forest-500 bg-forest-50 text-forest-700" : "border-paper-300 text-forest-900/65"}`}>{choice.title}</Link>)}</nav>
    {failed ? <><ErrorNote>This lesson preview could not be loaded. The preview server may be unavailable or the draft needs rebuilding.</ErrorNote>
      <button onClick={() => setRetry(n => n + 1)} className="mt-3 border border-paper-300 px-3 py-2 text-sm text-forest-700">Retry preview</button></>
      : preview ? <><PageHeader title={preview.lesson.title} /><LessonView key={preview.lesson.id} lesson={preview.lesson}
          imageUrl={imageId => api.previewImageUrl(preview.lesson.id, imageId)} /></> : <Loading />}
  </div>;
}
