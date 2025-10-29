"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type DecryptedTextProps = {
  phrases: readonly string[];
  /** Milliseconds between the start of each new phrase */
  interval?: number;
  /** Duration of the decrypt animation for each phrase (ms) */
  duration?: number;
  className?: string;
};

type ScrambleFrame = {
  from: string;
  to: string;
  startProgress: number;
  endProgress: number;
};

const RANDOM_CHARACTERS =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=<>?/[]{}";

export function DecryptedText({
  phrases,
  interval = 3600,
  duration = 1200,
  className,
}: DecryptedTextProps) {
  const sanitizedPhrases = useMemo(
    () =>
      phrases
        .map((phrase) => phrase.trim())
        .filter((phrase) => phrase.length > 0),
    [phrases],
  );

  const [displayed, setDisplayed] = useState(
    () => sanitizedPhrases[0] ?? "",
  );

  const indexRef = useRef(0);
  const resolvedRef = useRef(sanitizedPhrases[0] ?? "");
  const queueRef = useRef<ScrambleFrame[]>([]);
  const rafRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const mountedRef = useRef(true);

  const randomChar = useCallback(() => {
    const randomIndex = Math.floor(Math.random() * RANDOM_CHARACTERS.length);
    return RANDOM_CHARACTERS[randomIndex] ?? "";
  }, []);

  const cancelAnimation = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const cancelTimeout = useCallback(() => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const scrambleTo = useCallback(
    (nextText: string, animationDuration: number) => {
      cancelAnimation();

      const fromText = resolvedRef.current;
      const maxLength = Math.max(fromText.length, nextText.length);

      const queue: ScrambleFrame[] = Array.from({ length: maxLength }, (_, index) => {
        const fromChar = fromText[index] ?? "";
        const toChar = nextText[index] ?? "";

        if (!toChar) {
          return {
            from: fromChar,
            to: "",
            startProgress: 0,
            endProgress: 0.2 + Math.random() * 0.15,
          };
        }

        const start = Math.random() * 0.4;
        const end = Math.min(1, start + 0.45 + Math.random() * 0.25);

        return {
          from: fromChar,
          to: toChar,
          startProgress: start,
          endProgress: end,
        };
      });

      queueRef.current = queue;

      const totalDuration = Math.max(600, animationDuration);
      const startTime = performance.now();

      const step = (now: number) => {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / totalDuration);

        let output = "";
        let complete = 0;

        queueRef.current.forEach((item) => {
          if (progress >= item.endProgress) {
            complete += 1;
            output += item.to;
          } else if (progress >= item.startProgress) {
            if (item.to === "") {
              // Drop characters that disappear in the next phrase.
              return;
            }
            output += randomChar();
          } else {
            output += item.from;
          }
        });

        if (!mountedRef.current) {
          return;
        }

        setDisplayed(output);

        if (complete === queueRef.current.length) {
          resolvedRef.current = nextText;
          setDisplayed(nextText);
          rafRef.current = null;
          return;
        }

        rafRef.current = requestAnimationFrame(step);
      };

      rafRef.current = requestAnimationFrame((time) => step(time));
    },
    [cancelAnimation, randomChar],
  );

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      cancelAnimation();
      cancelTimeout();
    };
  }, [cancelAnimation, cancelTimeout]);

  useEffect(() => {
    if (!sanitizedPhrases.length) {
      setDisplayed("");
      resolvedRef.current = "";
      indexRef.current = 0;
      return;
    }

    resolvedRef.current = sanitizedPhrases[0];
    setDisplayed(sanitizedPhrases[0]);
    indexRef.current = 0;

    cancelAnimation();
    cancelTimeout();

    const cycle = () => {
      if (!mountedRef.current || sanitizedPhrases.length <= 1) {
        return;
      }

      indexRef.current = (indexRef.current + 1) % sanitizedPhrases.length;
      const nextPhrase = sanitizedPhrases[indexRef.current];
      scrambleTo(nextPhrase, duration);

      timeoutRef.current = window.setTimeout(cycle, interval);
    };

    timeoutRef.current = window.setTimeout(cycle, interval);

    return () => {
      cancelTimeout();
    };
  }, [sanitizedPhrases, interval, duration, scrambleTo, cancelAnimation, cancelTimeout]);

  return <span className={className}>{displayed}</span>;
}
