import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const targetUrl = __ENV.TARGET_URL || 'http://localhost:8888';
const duration = __ENV.SOAK_DURATION || '300';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: `${duration}s`, target: 20 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    errors: ['rate<0.01'],
    http_req_duration: ['p(95)<1000', 'p(99)<3000'],
    http_req_failed: ['rate<0.01'],
  },
};

const endpoints = [
  { method: 'GET', url: '/' },
  { method: 'GET', url: '/api/meta-snapshot' },
  { method: 'GET', url: '/api/tournaments' },
  { method: 'GET', url: '/api/lists' },
  { method: 'GET', url: '/api/cards/pilots' },
  { method: 'GET', url: '/api/cards/upgrades' },
  { method: 'GET', url: '/api/ships' },
];

export default function () {
  const ep = endpoints[Math.floor(Math.random() * endpoints.length)];
  const url = `${targetUrl}${ep.url}`;
  const res = http.get(url);

  check(res, {
    'status 200': (r) => r.status === 200,
  });

  errorRate.add(res.status !== 200);
  sleep(Math.random() * 0.3 + 0.1);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify({
      summary: {
        mode: 'soak',
        total_requests: data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 0,
        p95: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'] : 0,
        p99: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'] : 0,
        error_rate: data.metrics.http_req_failed ? data.metrics.http_req_failed.values.rate : 0,
      },
    }),
  };
}
