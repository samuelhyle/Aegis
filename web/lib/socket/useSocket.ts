"use client";

import { io, Socket } from "socket.io-client";
import { useEffect, useRef, useState, useCallback } from "react";
import type { InvestigationStreamEvent, InvestigationReport } from "@/types";

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:8000";

interface UseSocketOptions {
  autoConnect?: boolean;
  onEvent?: (event: unknown) => void;
}

export function useSocket(options: UseSocketOptions = {}) {
  const { autoConnect = true, onEvent } = options;
  const socketRef = useRef<Socket | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!autoConnect) return;

    const newSocket = io(SOCKET_URL, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });

    socketRef.current = newSocket;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSocket(newSocket);

    newSocket.on("connect", () => {
      setConnected(true);
      setError(null);
    });

    newSocket.on("disconnect", (reason) => {
      setConnected(false);
      if (reason !== "io client disconnect") {
        setError(`Disconnected: ${reason}`);
      }
    });

    newSocket.on("connect_error", (err) => {
      setError(err.message);
    });

    newSocket.on("investigation_event", (event: unknown) => {
      onEvent?.(event);
    });

    return () => {
      newSocket.disconnect();
      socketRef.current = null;
      setSocket(null);
    };
  }, [autoConnect, onEvent]);

  const connect = useCallback(() => {
    socketRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
  }, []);

  const emit = useCallback((event: string, data: unknown) => {
    socketRef.current?.emit(event, data);
  }, []);

  const on = useCallback((event: string, handler: (data: unknown) => void) => {
    socketRef.current?.on(event, handler);
    return () => socketRef.current?.off(event, handler);
  }, []);

  return { socket, connected, error, connect, disconnect, emit, on };
}

export function useInvestigationStream(patientId: string, question: string) {
  const [events, setEvents] = useState<InvestigationStreamEvent[]>([]);
  const [status, setStatus] = useState<"idle" | "connecting" | "streaming" | "completed" | "error">("idle");
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const { socket, connected, emit, on } = useSocket({ autoConnect: false });

  useEffect(() => {
    if (!socket || !connected) return;

    const cleanup = on("investigation_event", (event: unknown) => {
      const typedEvent = event as InvestigationStreamEvent;
      setEvents((prev) => [...prev, typedEvent]);

      switch (typedEvent.type) {
        case "agent_start":
          setStatus("streaming");
          break;
        case "investigation_completed":
          setStatus("completed");
          if (typedEvent.payload.report) {
            setReport(typedEvent.payload.report);
          }
          break;
        case "error":
          setStatus("error");
          break;
      }
    });

    emit("start_investigation", { patient_id: patientId, question });

    return () => {
      cleanup?.();
    };
  }, [socket, connected, patientId, question, emit, on]);

  const reset = useCallback(() => {
    setEvents([]);
    setStatus("idle");
    setReport(null);
  }, []);

  return { events, status, report, reset, connected };
}