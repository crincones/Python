import fs from 'fs';
const html = fs.readFileSync('receitas-amelina.html','utf8');

// --- 1. sanidade estrutural ---
const proibidos = [/<!DOCTYPE/i, /<html[\s>]/i, /<head[\s>]/i, /<body[\s>]/i];
proibidos.forEach(r => { if(r.test(html)) throw new Error('tag proibida: '+r); });
if(!/^<title>[^<]+<\/title>/.test(html)) throw new Error('sem <title> na primeira linha');

// hosts externos permitidos: apenas Google Fonts
const hosts = [...html.matchAll(/https?:\/\/([^\/"')\s]+)/g)].map(m=>m[1]);
const ok = new Set(['fonts.googleapis.com','fonts.gstatic.com']);
const ruins = [...new Set(hosts)].filter(h=>!ok.has(h));
if(ruins.length) throw new Error('host externo bloqueado pela CSP: '+ruins);

// toda cor precisa vir de token; procura literais fora dos blocos :root
const css = html.split('<style>')[1].split('</style>')[0];
const semRoot = css.replace(/:root[^{]*\{[^}]*\}/g,'').replace(/@media[^{]*\{\s*:root[^{]*\{[^}]*\}\s*\}/g,'');
const literais = [...semRoot.matchAll(/#[0-9a-fA-F]{3,8}\b/g)].map(m=>m[0]);
console.log('literais de cor fora dos tokens:', literais.length ? literais : 'nenhum ✓');

// --- 2. logica de calculo, extraida do proprio arquivo ---
const js = html.split('<script>')[1].split('</script>')[0];
const corpo = js.trim().replace(/^\(function\(\)\s*\{/,'').replace(/\}\)\(\);$/,'');
const stub = `
const alvo=()=>({appendChild(){},addEventListener(){},setAttribute(){},getAttribute:()=>null,style:{},innerHTML:'',textContent:'',className:'',querySelectorAll:()=>[]});
const document={getElementById:alvo,querySelector:alvo,querySelectorAll:()=>[],createElement:alvo};
const localStorage={getItem:()=>null,setItem(){}};
const window={confirm:()=>false,scrollTo(){},matchMedia:()=>({matches:false})};
${corpo}
return {conta, porUnidade, num, d};
`;
const api = new Function(stub)();

const esperado = {
  cafe: {ing:12.23875, emb:16.80, lote:29.03875, pote:7.2596875},
  capp: {ing:19.23775, emb:16.80, lote:36.03775, pote:9.0094375}
};
let falhas = 0;
for(const [id, e] of Object.entries(esperado)){
  const c = api.conta(id);
  for(const [k,v] of Object.entries(e)){
    const dif = Math.abs(c[k]-v);
    if(dif > 1e-9){ console.log('❌', id, k, 'obtido', c[k], 'esperado', v); falhas++; }
  }
  console.log(`${id}: lote R$ ${c.lote.toFixed(2)} | pote R$ ${c.pote.toFixed(2)} | lucro/pote R$ ${c.lucroPote.toFixed(2)} | margem ${(c.margem*100).toFixed(1)}% | markup ${c.markup.toFixed(2)}x`);
}

// --- 3. parser de numeros digitados ---
const casos = [['11,24',11.24],['2000',2000],['2.000',2000],['0,5',0.5],['7.99',7.99],['',0],['abc',0],['1.234,56',1234.56]];
casos.forEach(([entrada, esp])=>{
  const got = api.num(entrada);
  if(Math.abs(got-esp) > 1e-9){ console.log('❌ num("'+entrada+'") =',got,'esperado',esp); falhas++; }
});
console.log(falhas ? `\n${falhas} FALHA(S)` : '\nTudo confere ✓  (calculo + parser + CSP)');
