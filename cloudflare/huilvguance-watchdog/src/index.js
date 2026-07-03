const GITHUB_DISPATCH_URL =
  "https://api.github.com/repos/yichitorishen-ops/huilvguance/actions/workflows/pages.yml/dispatches";
const TARGET_HOURS = [0, 6, 13, 18];
const WINDOW_MINUTES = 120;

export default {
  async scheduled(event, env, ctx) {
    const scheduledTime = event.scheduledTime ? new Date(event.scheduledTime) : new Date();
    ctx.waitUntil(runWatchdog(env, scheduledTime, { dryRun: false }));
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    const now = url.searchParams.has("now") ? new Date(url.searchParams.get("now")) : new Date();
    if (Number.isNaN(now.getTime())) {
      return jsonResponse({ ok: false, error: "invalid_now" }, 400);
    }

    const result = await runWatchdog(env, now, { dryRun: true });
    return jsonResponse({ ok: true, ...result });
  },
};

async function runWatchdog(env, now, { dryRun }) {
  const decision = findActiveSlot(now);
  if (!decision.active) {
    console.log(JSON.stringify({ event: "no_active_slot", now: now.toISOString() }));
    return { dispatched: false, reason: "outside_capture_window", decision };
  }

  if (dryRun) {
    return { dispatched: false, reason: "dry_run", decision };
  }

  await dispatchWorkflow(env.GITHUB_TOKEN, decision.scheduledHour);
  console.log(
    JSON.stringify({
      event: "workflow_dispatched",
      scheduledHour: decision.scheduledHour,
      targetDate: decision.targetDate,
      now: now.toISOString(),
    }),
  );

  return { dispatched: true, decision };
}

async function dispatchWorkflow(token, scheduledHour) {
  if (!token) {
    throw new Error("Missing GITHUB_TOKEN secret");
  }

  const response = await fetch(GITHUB_DISPATCH_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "huilvguance-watchdog",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({
      ref: "main",
      inputs: {
        collect: "true",
        scheduled_hour: String(scheduledHour),
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`GitHub dispatch failed: ${response.status} ${await response.text()}`);
  }
}

function findActiveSlot(now) {
  const local = shanghaiParts(now);
  const currentMinute = localMinute(local);
  let best = null;

  for (const dayOffset of [-1, 0, 1]) {
    for (const hour of TARGET_HOURS) {
      const targetMinute =
        Date.UTC(local.year, local.month - 1, local.day + dayOffset, hour, 0) / 60000;
      const deltaMinutes = currentMinute - targetMinute;
      if (deltaMinutes < -WINDOW_MINUTES || deltaMinutes > WINDOW_MINUTES) {
        continue;
      }

      if (!best || Math.abs(deltaMinutes) < Math.abs(best.deltaMinutes)) {
        best = { scheduledHour: hour, targetMinute, deltaMinutes };
      }
    }
  }

  if (!best) {
    return { active: false, localTime: formatLocalParts(local) };
  }

  return {
    active: true,
    scheduledHour: best.scheduledHour,
    targetDate: formatPseudoLocalDate(best.targetMinute),
    deltaMinutes: best.deltaMinutes,
    localTime: formatLocalParts(local),
  };
}

function shanghaiParts(now) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(now);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return {
    year: Number(values.year),
    month: Number(values.month),
    day: Number(values.day),
    hour: Number(values.hour),
    minute: Number(values.minute),
  };
}

function localMinute(parts) {
  return Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute) / 60000;
}

function formatLocalParts(parts) {
  return `${parts.year}-${pad(parts.month)}-${pad(parts.day)}T${pad(parts.hour)}:${pad(
    parts.minute,
  )}+08:00`;
}

function formatPseudoLocalDate(minute) {
  const date = new Date(minute * 60000);
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
