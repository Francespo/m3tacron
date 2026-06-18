import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const targetUrl = __ENV.TARGET_URL || 'http://localhost:8888';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m', target: 10 },
    { duration: '30s', target: 20 },
    { duration: '1m', target: 10 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    errors: ['rate<0.01'],
    http_req_duration: ['p(95)<1000', 'p(99)<3000'],
    http_req_failed: ['rate<0.01'],
  },
};

const endpoints = [
  { method: 'GET', url: '/', weight: 1 },
  { method: 'GET', url: '/api/meta-snapshot', weight: 10 },
  { method: 'GET', url: '/api/tournaments', weight: 5 },
  { method: 'GET', url: '/api/lists', weight: 5 },
  { method: 'GET', url: '/api/cards/pilots', weight: 3 },
  { method: 'GET', url: '/api/cards/upgrades', weight: 3 },
  { method: 'GET', url: '/api/ships', weight: 3 },
];

const totalWeight = endpoints.reduce((sum, ep) => sum + ep.weight, 0);

function pickEndpoint() {
  let r = Math.random() * totalWeight;
  for (const ep of endpoints) {
    r -= ep.weight;
    if (r <= 0) return ep;
  }
  return endpoints[0];
}

export default function () {
  const ep = pickEndpoint();
  const url = `${targetUrl}${ep.url}`;
  const res = http.get(url);

  check(res, {
    'status 200': (r) => r.status === 200,
  });

  errorRate.add(res.status !== 200);
  sleep(Math.random() * 0.5 + 0.1);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify({
      summary: {
        metrics: data.metrics,
        total_requests: data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 0,
        p95: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'] : 0,
        p99: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'] : 0,
        error_rate: data.metrics.http_req_failed ? data.metrics.http_req_failed.values.rate : 0,
      },
    }),
  };
}
