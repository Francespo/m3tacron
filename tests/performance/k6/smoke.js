import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const targetUrl = __ENV.TARGET_URL || 'http://localhost:8888';

const errorRate = new Rate('errors');
const requestTrend = new Trend('request_duration');

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    errors: ['rate<0.01'],
    http_req_duration: ['p(95)<1000', 'p(99)<3000'],
    http_req_failed: ['rate<0.01'],
  },
};

const endpoints = [
  { method: 'GET', url: '/', name: 'root' },
  { method: 'GET', url: '/api/meta-snapshot', name: 'meta-snapshot' },
  { method: 'GET', url: '/api/tournaments', name: 'tournaments' },
  { method: 'GET', url: '/api/lists', name: 'lists' },
  { method: 'GET', url: '/api/cards/pilots', name: 'cards-pilots' },
  { method: 'GET', url: '/api/cards/upgrades', name: 'cards-upgrades' },
  { method: 'GET', url: '/api/ships', name: 'ships' },
];

export default function () {
  for (const ep of endpoints) {
    const url = `${targetUrl}${ep.url}`;
    const res = http.get(url, { tags: { name: ep.name } });

    check(res, {
      [`${ep.name} status 200`]: (r) => r.status === 200,
    });

    errorRate.add(res.status !== 200);
    requestTrend.add(res.timings.duration);

    sleep(0.5);
  }
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify({
      summary: {
        metrics: data.metrics,
        total_requests: data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 0,
        checks_passed: data.metrics.checks ? data.metrics.checks.values.passes : 0,
        checks_failed: data.metrics.checks ? data.metrics.checks.values.fails : 0,
        p95: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'] : 0,
        p99: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'] : 0,
        error_rate: data.metrics.http_req_failed ? data.metrics.http_req_failed.values.rate : 0,
      },
    }),
  };
}
