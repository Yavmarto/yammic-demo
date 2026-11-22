"""Run a frozen, hand-labelled Dutch challenge set against local providers."""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from app.ai.providers import get_provider
from app.ai.providers.ollama import OllamaProvider
from app.ai.span import span_matches
from app.ai.types import FieldDef
from eval import gold as gold_mod
from eval.harness import _eq

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', required=True, choices=['rules', 'ollama'])
    ap.add_argument('--timeout', type=float, default=240.0, help='Ollama request timeout per document')
    args = ap.parse_args()
    data = json.loads((HERE / 'dataset.json').read_text())
    fields = {x['id']: FieldDef.from_api(x) for x in gold_mod.load_fields()}
    provider = get_provider(args.provider)
    if args.provider == 'ollama':
        provider = OllamaProvider(model=provider.model, timeout=args.timeout)
    ok, reason = provider.available()
    if not ok:
        print(f'Unavailable: {reason}', file=sys.stderr)
        return 2
    counts = defaultdict(lambda: {'support':0,'correct':0,'tp':0,'fp':0,'fn':0,'goldAbstain':0,'correctAbstain':0})
    docs=[]; exact=0; expected_proposals=0; invalid=0; failures=[]; started=time.perf_counter(); prompt_meta=None
    for d in data['documents']:
        t=time.perf_counter()
        try:
            result=provider.extract(d['text'],d['type'],list(fields.values()))
        except Exception as exc:
            timeout='timeout' in str(exc).casefold() or isinstance(exc, TimeoutError)
            failures.append({'documentId':d['id'],'kind':'timeout' if timeout else type(exc).__name__,'message':str(exc)[:300]})
            docs.append({'documentId':d['id'],'status':'timeout' if timeout else 'error','durationMs':round((time.perf_counter()-t)*1000)})
            continue
        pred=result.by_field(); row={'documentId':d['id'],'status':'ok','durationMs':round((time.perf_counter()-t)*1000),'fields':{}}
        prompt_meta = {'version':result.metadata.prompt_version,'sha256':result.metadata.prompt_hash}
        invalid += sum(1 for proposal in result.proposals if proposal.status=='proposed' and
                       (not proposal.evidence or any(not span_matches(d['text'],e) for e in proposal.evidence)))
        for fid,g in d['fields'].items():
            p=pred.get(fid); c=counts[fid]; c['support']+=1
            isprop=p is not None and p.status=='proposed'
            same=isprop and _eq(fid,g.get('value'),p.normalized_value)
            decided=(isprop== (g['status']=='proposed')) and (g['status']!='proposed' or same)
            c['correct']+=int(decided)
            if g['status']=='abstained':
                c['goldAbstain']+=1
                if not isprop: c['correctAbstain']+=1
                else: c['fp']+=1
            elif not isprop: c['fn']+=1
            elif same: c['tp']+=1
            else: c['fp']+=1; c['fn']+=1
            gold_span=g.get('evidence'); span_exact=False
            if g['status']=='proposed':
                expected_proposals+=1
                if isprop and p.evidence:
                    span_exact=any(e.text==gold_span for e in p.evidence)
                exact+=int(span_exact)
            bad=bool(isprop and (not p.evidence or any(not span_matches(d['text'],e) for e in p.evidence)))
            row['fields'][fid]={'goldStatus':g['status'],'predictedStatus':p.status if p else 'missing','correctDecision':decided,'goldValue':g.get('value'),'predictedValue':p.normalized_value if isprop else None,'exactSpan':span_exact,'invalidSourceSpan':bad}
        docs.append(row)
    per={}
    for fid,c in counts.items():
        den=c['tp']+c['fp']; recden=c['tp']+c['fn']; precision=c['tp']/den if den else None; recall=c['tp']/recden if recden else None
        per[fid]={**c,'decisionAccuracy':round(c['correct']/c['support'],4),'precision':round(precision,4) if precision is not None else None,'recall':round(recall,4) if recall is not None else None,'f1':round(2*precision*recall/(precision+recall),4) if precision is not None and recall is not None and precision+recall else 0.0,'correctAbstentionDenominator':c['goldAbstain']}
    out={'schemaVersion':1,'generatedAt':datetime.now(UTC).isoformat(),'provider':{'name':provider.name,'model':provider.model,'paid':False},'prompt':prompt_meta,'limits':{'timeoutSecondsPerDocument':args.timeout if args.provider=='ollama' else None,'temperature':0 if args.provider=='ollama' else None,'seed':42 if args.provider=='ollama' else None},'dataset':{'name':data['name'],'path':'backend/eval/challenge/dataset.json','documentCount':len(data['documents'])},'summary':{'documents':len(data['documents']),'completedDocuments':sum(x['status']=='ok' for x in docs),'timeouts':sum(x['kind']=='timeout' for x in failures),'decisionAccuracy':round(sum(c['correct'] for c in counts.values())/sum(c['support'] for c in counts.values()),4) if counts else None,'exactSpanAgreement':f'{exact}/{expected_proposals}','invalidSourceSpans':invalid,'durationMs':round((time.perf_counter()-started)*1000)},'fields':per,'documents':docs,'failures':failures}
    outdir=HERE/'results'/args.provider; outdir.mkdir(parents=True,exist_ok=True)
    outpath=outdir/'latest.json'; outpath.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    lines=[f"# Dutch challenge — {provider.name} ({provider.model})",'',f"Dataset: `{data['name']}` · {len(data['documents'])} documents",f"Completed: {out['summary']['completedDocuments']}/{len(docs)} · timeouts: {out['summary']['timeouts']} · limits: timeout {args.timeout:g}s/document; temperature 0; seed 42",f"Decision accuracy: {out['summary']['decisionAccuracy']} · exact-span agreement: {exact}/{expected_proposals} · invalid-source spans: {invalid}",'','| Field | Accuracy | F1 | Correct abstentions |','|---|---:|---:|---:|']
    for fid,v in per.items():
        f1 = '—' if v['f1'] is None else f"{v['f1']:.3f}"
        lines.append(f"| {fid} | {v['decisionAccuracy']:.3f} | {f1} | {v['correctAbstain']}/{v['correctAbstentionDenominator']} |")
    (outdir/'latest.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines)); print(f'Wrote {outpath}')
    return 1 if failures else 0

if __name__=='__main__': raise SystemExit(main())
