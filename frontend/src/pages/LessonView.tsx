import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, ZoomIn, ZoomOut } from "lucide-react";
import type { Lesson, LessonAsset, LessonBlock, LessonCitation, LessonFigure, LessonStep } from "../api/types";
import { sourceCaption } from "../api/types";

function Sources({ sources }: { sources: LessonCitation[] }) {
  return <p className="mt-4 text-xs leading-relaxed text-forest-900/50">Source: {[...new Set(sources.map(s =>
    `${sourceCaption(s) ?? s.source_file}${s.surface === "notes" ? " · notes" : ""}`))].join("; ")}</p>;
}

function MethodSteps({ steps }: { steps: LessonStep[] }) {
  return <ol className="space-y-5">{steps.map((step, index) => <li key={index} className="grid grid-cols-[1.5rem_1fr] gap-3">
    <span className="pt-0.5 text-sm font-medium tabular-nums text-forest-500">{index + 1}.</span>
    <div className="min-w-0"><h4 className="font-medium">{step.title}</h4><p className="mt-1 text-sm leading-relaxed text-forest-900/75">{step.text}</p>
      {step.equation ? <p className="mt-2 break-words border-l-2 border-forest-500 pl-3 font-mono text-sm leading-relaxed text-forest-700">{step.equation}</p> : null}
    </div></li>)}</ol>;
}

function FigureView({ figure, asset, imageUrl }: { figure: LessonFigure; asset: LessonAsset; imageUrl: (id: string) => string }) {
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [open, setOpen] = useState(false);
  const url = imageUrl(asset.image_id) + (retry ? `?retry=${retry}` : "");
  return <figure className="my-4">
    {failed ? <div role="alert" className="border border-clay-500/35 bg-paper-50 p-5 text-sm">
      <p>This diagram could not be loaded.</p><p className="mt-1 text-forest-900/65">{figure.caption}. The source reference is shown below.</p>
      <button onClick={() => { setFailed(false); setRetry(n => n + 1); }} className="mt-3 border border-paper-300 px-3 py-1.5 text-forest-700">Retry image</button>
    </div> : <Dialog.Root open={open} onOpenChange={value => { setOpen(value); setZoom(1); }}>
      <div className="border border-paper-200 bg-white p-4 sm:p-6">
        <img src={url} width={asset.width} height={asset.height} loading="lazy" decoding="async" alt={figure.alt}
          onError={() => setFailed(true)} className="mx-auto h-auto w-full max-w-lg bg-white" />
        <Dialog.Trigger asChild><button className="mx-auto mt-3 flex items-center gap-2 px-3 py-2 text-xs text-forest-700 hover:bg-paper-100">
          <ZoomIn size={15} aria-hidden /> Enlarge diagram</button></Dialog.Trigger>
      </div>
      <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-50 bg-forest-900/70" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-4xl -translate-x-1/2 -translate-y-1/2 flex-col border border-paper-300 bg-paper-50 p-4 sm:p-6">
          <div className="flex items-start justify-between gap-4"><div className="min-w-0"><Dialog.Title className="font-semibold">{figure.caption}</Dialog.Title>
            <Dialog.Description className="mt-1 text-xs leading-relaxed text-forest-900/65">{figure.alt}</Dialog.Description></div>
            <Dialog.Close asChild><button aria-label="Close enlarged diagram" className="shrink-0 p-1.5"><X size={18} /></button></Dialog.Close></div>
          <div className="my-3 flex items-center gap-3 text-xs"><button disabled={zoom <= 1} aria-label="Zoom out" onClick={() => setZoom(z => Math.max(1, z - .5))} className="border border-paper-300 p-2 disabled:opacity-35"><ZoomOut size={16} /></button>
            <span className="tabular-nums">{Math.round(zoom * 100)}%</span><button disabled={zoom >= 3} aria-label="Zoom in" onClick={() => setZoom(z => Math.min(3, z + .5))} className="border border-paper-300 p-2 disabled:opacity-35"><ZoomIn size={16} /></button></div>
          <div tabIndex={0} role="region" aria-label="Enlarged source diagram" className="min-h-0 overflow-auto border border-paper-200 bg-white">
            <img src={url} alt={figure.alt} width={asset.width} height={asset.height} className="h-auto max-w-none bg-white" style={{ width: `${zoom * 100}%` }} />
          </div>
        </Dialog.Content></Dialog.Portal>
    </Dialog.Root>}
    <figcaption className="mt-2 text-sm font-medium">{figure.caption}</figcaption><Sources sources={[figure.source]} />
  </figure>;
}

export function LessonView({ lesson, imageUrl }: { lesson: Lesson; imageUrl: (id: string) => string }) {
  const assets = new Map(lesson.assets.map(asset => [asset.image_id, asset]));
  function blockView(block: LessonBlock) {
    if (block.type === "figure") return <FigureView key={block.id} figure={block} asset={assets.get(block.image_id)!} imageUrl={imageUrl} />;
    if (block.type === "text") return <div key={block.id}>{block.paragraphs.map((text, i) => <p key={i} className="mt-3 text-sm leading-7 text-forest-900/80">{text}</p>)}<Sources sources={block.sources} /></div>;
    if (block.type === "formula") return <div key={block.id}>
      <p className="my-3 break-words border-l-2 border-forest-500 bg-paper-50 px-4 py-4 font-mono text-lg text-forest-700 sm:text-xl">{block.expression}</p>
      <div className="grid gap-5 sm:grid-cols-2"><div><h4 className="text-xs font-semibold uppercase tracking-wide text-forest-500">Quantities</h4><ul className="mt-2 space-y-2 text-sm leading-relaxed">{block.variables.map(v => <li key={v}>{v}</li>)}</ul></div>
        <div><h4 className="text-xs font-semibold uppercase tracking-wide text-forest-500">When it applies</h4><ul className="mt-2 space-y-2 text-sm leading-relaxed text-forest-900/75">{block.conditions.map(c => <li key={c}>{c}</li>)}</ul></div></div><Sources sources={block.sources} />
    </div>;
    if (block.type === "steps") return <div key={block.id}><MethodSteps steps={block.steps} /><Sources sources={block.sources} /></div>;
    return <div key={block.id}>
      <p className="text-sm leading-7">{block.prompt}</p><div className="my-4 border border-paper-200 bg-paper-50 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-forest-500">Given</h4><ul className="mt-2 space-y-1 text-sm leading-relaxed">{block.givens.map(g => <li key={g}>{g}</li>)}</ul>
        <p className="mt-3 border-t border-paper-200 pt-3 text-sm font-medium">Find: {block.target}</p></div>
      {block.figures.filter(f => f.role !== "solution_diagram").map(f => <FigureView key={f.id} figure={f} asset={assets.get(f.image_id)!} imageUrl={imageUrl} />)}
      <MethodSteps steps={block.steps} />
      {block.figures.filter(f => f.role === "solution_diagram").map(f => <FigureView key={f.id} figure={f} asset={assets.get(f.image_id)!} imageUrl={imageUrl} />)}
      <p className="mt-5 border-l-2 border-forest-500 pl-3 font-medium text-forest-700">{block.result}</p><Sources sources={block.sources} />
    </div>;
  }
  const stageNames = { overview: "Understand the topic", baseline: "Baseline method", recognition: "Recognize the pattern", shortcut: "Specialized shortcut" };
  return <div>
    <p className="mb-6 max-w-2xl text-sm leading-7 text-forest-900/75">{lesson.introduction}</p>
    <div className="space-y-6">{lesson.sections.map(section => <section key={section.id} aria-labelledby={`section-${section.id}`} className="border border-paper-200 bg-white px-5 py-5 sm:px-6 sm:py-6">
      <p className="mb-2 text-[11px] font-medium uppercase tracking-widest text-forest-500">{stageNames[section.stage]}</p>
      <h2 id={`section-${section.id}`} className="mb-5 text-lg font-semibold">{section.title}</h2>
      <div className="space-y-6">{section.blocks.map(blockView)}</div>
    </section>)}</div>
  </div>;
}
