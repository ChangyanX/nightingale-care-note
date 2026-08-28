"use client";

import { InputHTMLAttributes, useRef, useState } from "react";

export function PasswordField({ label, ...props }: { label: string } & Omit<InputHTMLAttributes<HTMLInputElement>, "type">) {
  const [visible, setVisible] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function toggle() {
    const input = inputRef.current;
    const start = input?.selectionStart ?? null;
    const end = input?.selectionEnd ?? null;
    setVisible((value) => !value);
    requestAnimationFrame(() => {
      input?.focus();
      if (start !== null && end !== null) input?.setSelectionRange(start, end);
    });
  }

  return <label className="password-label">{label}<span className="password-control"><input {...props} ref={inputRef} type={visible ? "text" : "password"} /><button type="button" onClick={toggle} aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`} aria-pressed={visible}>{visible ? "Hide" : "Show"}</button></span></label>;
}
