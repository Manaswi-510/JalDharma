/**
 * Jal Dharma AI - useLiveData Hook
 * A generic React hook that fetches from the API, manages loading/error state,
 * and optionally polls on an interval.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useLiveData(api.overview);
 *   const { data, loading, error } = useLiveData(() => api.predictions(villageId, 14), [villageId]);
 */

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * @param {Function} fetcher   - A function that returns a Promise (e.g. api.overview)
 * @param {Array}    deps      - Re-fetch when these change (like useEffect deps)
 * @param {Object}   options
 * @param {number}   options.pollMs      - If > 0, re-fetch every pollMs milliseconds
 * @param {any}      options.fallback    - Value to use while loading (default null)
 */
export function useLiveData(fetcher, deps = [], { pollMs = 0, fallback = null } = {}) {
  const [data, setData] = useState(fallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetch_();

    if (pollMs > 0) {
      timerRef.current = setInterval(fetch_, pollMs);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetch_, pollMs]);

  return { data, loading, error, refetch: fetch_ };
}

// ── Convenience wrappers ──────────────────────────────────────────────────────
export { useLiveData as default };
