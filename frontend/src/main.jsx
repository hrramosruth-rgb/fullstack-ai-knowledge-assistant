import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

async function api(path,body){
  const response=await fetch('/api/'+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const data=await response.json();
  if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'Check the required fields and length limits.');
  return data;
}
function App(){
  const [docs,setDocs]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const [question,setQuestion]=useState(''),[history,setHistory]=useState([]),[asking,setAsking]=useState(false);
  const [title,setTitle]=useState(''),[text,setText]=useState(''),[saving,setSaving]=useState(false),[notice,setNotice]=useState('');
  const askingLock=useRef(false),savingLock=useRef(false);
  useEffect(()=>{let active=true;api('documents').then(data=>{if(active)setDocs(data)}).catch(error=>{if(active)setError(error.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[]);
  async function ask(event){
    event.preventDefault();if(askingLock.current||!question.trim())return;
    askingLock.current=true;setAsking(true);setError('');const asked=question;
    try{const response=await api('ask',{question:asked});setHistory(previous=>[...previous,{question:asked,...response}]);setQuestion('')}
    catch(error){setError(error.message)}finally{askingLock.current=false;setAsking(false)}
  }
  async function ingest(event){
    event.preventDefault();if(savingLock.current)return;
    savingLock.current=true;setSaving(true);setError('');setNotice('');
    try{const doc=await api('documents',{title,text});setDocs(previous=>[...previous.filter(item=>item.id!==doc.id),doc]);setTitle('');setText('');setNotice('Document indexed. Ask a question using its key terms.')}
    catch(error){setError(error.message)}finally{savingLock.current=false;setSaving(false)}
  }
  return <main className="app"><aside><a href="#chat" className="brand"><span className="symbol">✦</span>Sourcebook</a><p className="aside-label">YOUR KNOWLEDGE LIBRARY</p><h2>Documents <span>{docs.length}</span></h2>{loading?<p role="status">Loading library…</p>:docs.length===0?<p className="muted">No documents yet. Add text below to begin.</p>:<ul className="documents">{docs.map(doc=><li key={doc.id}><span className="file-icon">▤</span><div><strong>{doc.title}</strong><small>{doc.characters.toLocaleString()} characters · Indexed</small></div></li>)}</ul>}
      <form className="ingest" onSubmit={ingest}><h2>Add a document</h2><label>Title<input required maxLength={120} value={title} onChange={event=>setTitle(event.target.value)} placeholder="e.g. Project notes"/></label><label>Plain text<textarea required maxLength={50000} rows={5} value={text} onChange={event=>setText(event.target.value)} placeholder="Paste a source passage…"/></label><button disabled={saving||!title.trim()||!text.trim()}>{saving?'Indexing…':'Index document'}</button><p className="muted">Up to 50,000 characters. Stored locally in SQLite.</p></form><p className="aside-foot">Independent portfolio demonstration<br/>Code created in October 2026<br/>Simulated development timeline</p></aside>
    <section id="chat" className="workspace"><header><span>Workspace / Knowledge assistant</span><span className="badge">● OFFLINE EXTRACTIVE</span></header><div className="intro"><p className="eyebrow">ANSWERS YOU CAN TRACE</p><h1>Start with a source.</h1><p>Search your documents and see the exact passage behind each answer.</p><div className="mode-note"><span>✧</span><p><strong>Deterministic demo mode</strong><br/>Keyword retrieval returns a source quote. This demo does not call an LLM or generate new facts.</p></div></div>
      <div className="suggestions"><span>Try asking</span>{['When are release reviews?','What are support hours?','How does project discovery begin?'].map(prompt=><button key={prompt} className="chip" type="button" disabled={asking} onClick={()=>setQuestion(prompt)}>{prompt} ↗</button>)}</div>
      <div role="log" aria-label="Question and answer history" className="conversation">{history.length===0?<div className="empty"><span>✦</span><h2>Your next answer starts here</h2><p>Ask about the demo handbook or add your own document.</p></div>:history.map((entry,index)=><article className="exchange" key={index}><div className="question"><small>YOU ASKED</small><p>{entry.question}</p></div><div className="answer"><small>{entry.supported?'SOURCE PASSAGE':'NO MATCHING SOURCE'}</small><p>{entry.answer}</p>{entry.citations.map(citation=><details key={citation.document_id+'-'+citation.chunk}><summary>▤ {citation.title} · passage {citation.chunk+1}</summary><blockquote>{citation.quote}</blockquote><small>Document ID: {citation.document_id}</small></details>)}</div></article>)}</div>
      <div aria-live="polite">{error&&<p role="alert" className="error">Request failed: {error}</p>}{notice&&<p className="notice">{notice}</p>}{asking&&<p role="status">Finding a source passage…</p>}</div>
      <form className="composer" onSubmit={ask}><label className="sr-only" htmlFor="question">Question</label><input id="question" required maxLength={500} value={question} onChange={event=>setQuestion(event.target.value)} placeholder="Ask a question about your documents…"/><button disabled={asking||!question.trim()}>{asking?'Searching…':'Ask ↗'}</button></form><p className="disclaimer">Quotes are evidence from supplied documents, not verified facts. No external network calls or paid credentials.</p>
    </section></main>;
}
createRoot(document.getElementById('root')).render(<App/>);
