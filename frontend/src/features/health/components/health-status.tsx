"use client";

import { useEffect, useState } from "react";

import { getHealth } from "../services/get-health";
import type { HealthResponse } from "../types/health";

type ConnectionState =
  | { status: "loading" }
  | { status: "connected"; data: HealthResponse }
  | { status: "error"; message: string };

export function HealthStatus() {
  const [connection, setConnection] =
    useState<ConnectionState>({
      status: "loading",
    });

  useEffect(() => {
    async function checkHealth() {
      try {
        const data = await getHealth();

        setConnection({
          status: "connected",
          data,
        });
      } catch (error) {
        setConnection({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "不明なエラーが発生しました。",
        });
      }
    }

    void checkHealth();
  }, []);

  if (connection.status === "loading") {
    return (
      <section>
        <h2>バックエンド接続状態</h2>
        <p>確認中...</p>
      </section>
    );
  }

  if (connection.status === "error") {
    return (
      <section>
        <h2>バックエンド接続状態</h2>
        <p>接続失敗</p>
        <p>{connection.message}</p>
      </section>
    );
  }

  return (
    <section>
      <h2>バックエンド接続状態</h2>
      <p>接続成功</p>

      <dl>
        <div>
          <dt>API Status</dt>
          <dd>{connection.data.status}</dd>
        </div>

        <div>
          <dt>Service</dt>
          <dd>{connection.data.service}</dd>
        </div>
      </dl>
    </section>
  );
}