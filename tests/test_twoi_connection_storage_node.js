'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');

function storage() {
  const values = new Map();
  return {getItem:k => values.get(k) ?? null, setItem:(k,v) => values.set(k,String(v))};
}

for (const file of ['2i/index.html', '2i/writers-room-v22.html']) {
  const html = fs.readFileSync(path.join(root,file),'utf8');
  const start = html.search(/(?:let|const) LLM_KEY =/);
  const end = html.indexOf('let llmCfg =', start);
  assert(start >= 0 && end > start, file);
  const localStorage=storage(), sessionStorage=storage();
  const context=vm.createContext({localStorage,sessionStorage,location:{origin:'http://reach.test',protocol:'http:'}});
  vm.runInContext(html.slice(start,end),context);
  vm.runInContext("LLM_KEY='pubcast2i_llm_v2_alice'",context);
  vm.runInContext(`{
    const cfg=defaultLLM();
    cfg.claude.apiKey='claude-test-secret';cfg.openai.apiKey='openai-test-secret';
    cfg.pubpartner.token='reach-test-secret';cfg.openai.model='selected-model';saveLLM(cfg);
  }`,context);
  const key='pubcast2i_llm_v2_alice';
  assert(!/test-secret/.test(localStorage.getItem(key)),file+' wrote secrets to permanent browser storage');
  assert(/test-secret/.test(sessionStorage.getItem(key)),file+' lost the tab connection settings');
  assert.equal(vm.runInContext('loadLLM().openai.apiKey',context),'openai-test-secret');
  // Migrate an old owner-scoped persistent config, keeping it usable in this tab.
  const old=JSON.parse(sessionStorage.getItem(key));
  localStorage.setItem(key,JSON.stringify(old));
  const fresh=storage();context.sessionStorage=fresh;
  assert.equal(vm.runInContext('loadLLM().claude.apiKey',context),'claude-test-secret');
  assert(!/test-secret/.test(localStorage.getItem(key)),file+' failed to scrub a legacy persistent config');
  context.sessionStorage=storage();
  assert.equal(vm.runInContext('loadLLM().openai.apiKey',context),'');
  assert.equal(vm.runInContext('loadLLM().openai.model',context),'selected-model');
  vm.runInContext("LLM_KEY='pubcast2i_llm_v2_bob'",context);
  assert.equal(vm.runInContext('loadLLM().claude.apiKey',context),'');
  console.log('PASS: '+file+' keeps secrets tab-only, migrates old settings, retains model choices and isolates owners');
}
