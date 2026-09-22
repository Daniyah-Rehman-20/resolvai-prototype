"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { X, Inbox, ArrowUpRight, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { label } from "@/lib/utils";
export function Badge({ value }: { value: string }) {
  return (
    <span className={`badge status-${value.toLowerCase()}`}>
      {label(value)}
    </span>
  );
}
export function Empty({
  title = "Nothing here yet",
  detail = "New items will appear here when they are available.",
}: {
  title?: string;
  detail?: string;
}) {
  return (
    <div className="empty">
      <Inbox size={30} />
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}
export function PageTitle({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="heading-actions">{children}</div>
    </div>
  );
}
export function Panel({
  title,
  subtitle,
  children,
  action,
  className = "",
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function MoreLink({
  href,
  children = "View all",
}: {
  href: string;
  children?: ReactNode;
}) {
  return (
    <Link className="text-link" href={href}>
      {children}
      <ArrowUpRight size={15} />
    </Link>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog ref={ref} onCancel={onClose} aria-labelledby="modal-title">
      <div className="modal-heading">
        <h2 id="modal-title">{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function Busy({ text = "Loading workspace…" }: { text?: string }) {
  return (
    <div className="busy" role="status">
      <LoaderCircle className="spin" size={24} />
      {text}
    </div>
  );
}
