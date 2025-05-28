import http from 'k6/http';
import { check, sleep } from 'k6';

eml = ""
pswd = ""

export let options = {
  stages: [
    { duration: '15s', target: 5 },
    { duration: '15s', target: 5 },
  ],
};

export function setup() {
  const loginRes = http.post('http://127.0.0.1:5000/oauth/token', JSON.stringify({
    email: eml,
    password: pswd,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(loginRes, {
    'login succeeded': (res) => res.status === 200,
    'token received': (res) => res.json('access_token') !== '',
  });
  console.log(`Login response: ${JSON.stringify(loginRes.json())}`);
  const token = loginRes.json('access_token');
  return { token };
}

export default function (data) {
  const headers = {
    headers: {
      Authorization: `Bearer ${data.token}`,
    },
  };

  const res = http.get('http://127.0.0.1:5000/fitness/wod', headers);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
