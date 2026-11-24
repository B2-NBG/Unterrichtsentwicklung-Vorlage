
/* Minimaler PDF-Writer (Text und Linien) – keine externen Bibliotheken. Schrift: Helvetica/WinAnsi,
   auf Seiten mit Schriften fürs Zeichnen (style#zeichen-schriften) Zeichenschrift als eingebettete TrueType-Schrift (Type0, Identity-H).
   Koordinaten in mm, Ursprung oben links; y = Grundlinie des Textes. */
var PDFW=(function(){
var WR=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584, 0, 556, 0, 222, 556, 333, 1000, 556, 556, 333, 1000, 667, 333, 1000, 0, 611, 0, 0, 222, 222, 333, 333, 350, 556, 1000, 333, 1000, 500, 333, 944, 0, 500, 667, 278, 333, 556, 556, 556, 556, 260, 556, 333, 737, 370, 556, 584, 333, 737, 552, 400, 549, 333, 333, 333, 576, 537, 333, 333, 333, 365, 556, 834, 834, 834, 611, 667, 667, 667, 667, 667, 667, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278, 722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611, 556, 556, 556, 556, 556, 556, 889, 500, 556, 556, 556, 556, 278, 278, 278, 278, 556, 556, 556, 556, 556, 556, 556, 549, 611, 556, 556, 556, 556, 500, 556, 500],WB=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611, 975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556, 333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584, 0, 556, 0, 278, 556, 500, 1000, 556, 556, 333, 1000, 667, 333, 1000, 0, 611, 0, 0, 278, 278, 500, 500, 350, 556, 1000, 333, 1000, 556, 333, 944, 0, 500, 667, 278, 333, 556, 556, 556, 556, 280, 556, 333, 737, 370, 556, 584, 333, 737, 552, 400, 549, 333, 333, 333, 576, 556, 333, 333, 333, 365, 556, 834, 834, 834, 611, 722, 722, 722, 722, 722, 722, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278, 722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611, 556, 556, 556, 556, 556, 556, 889, 556, 556, 556, 556, 556, 278, 278, 278, 278, 611, 611, 611, 611, 611, 611, 611, 549, 611, 611, 611, 611, 611, 556, 611, 556];
var CP={0x20AC:0x80,0x201A:0x82,0x0192:0x83,0x201E:0x84,0x2026:0x85,0x2020:0x86,0x2021:0x87,0x02C6:0x88,0x2030:0x89,0x0160:0x8A,0x2039:0x8B,0x0152:0x8C,0x017D:0x8E,0x2018:0x91,0x2019:0x92,0x201C:0x93,0x201D:0x94,0x2022:0x95,0x2013:0x96,0x2014:0x97,0x02DC:0x98,0x2122:0x99,0x0161:0x9A,0x203A:0x9B,0x0153:0x9C,0x017E:0x9E,0x0178:0x9F};
var REPL={'−':'\x96','≈':'ca. ','≥':'>=','≤':'<=','→':'->','←':'<-','‑':'-',' ':' ',' ':' ',' ':' ',' ':' ','­':'','✕':'x','✓':'v','▲':'^','▼':'v'};
var MM=72/25.4;
REPL['⌀']='\xD8';REPL['☐']='[ ]';REPL['☑']='[x]';REPL['□']='[ ]';REPL['✗']='x';REPL['✔']='v';REPL['➜']='->';REPL['▶']='>';
REPL['∥']='||';REPL['⟂']='_|_';REPL['∠']='Winkel ';REPL['○']='o';'①②③④⑤⑥⑦⑧⑨⑩'.split('').forEach(function(c,i){REPL[c]='('+(i+1)+')'});
/* ---- Schrift fürs Zeichnen (TrueType aus den eingebetteten WOFF-Teilmengen) ---- */
var TT=null;   /* {r: Schrift normal, b: fett} oder null = Helvetica */
function u16(b,o){return (b[o]<<8)|b[o+1]}
function i16(b,o){var v=u16(b,o);return v>32767?v-65536:v}
function u32(b,o){return ((b[o]<<24)>>>0)+(b[o+1]<<16)+(b[o+2]<<8)+b[o+3]}
function strm(u,ds){return new Response(new Blob([u]).stream().pipeThrough(ds)).arrayBuffer().then(function(a){return new Uint8Array(a)})}
function woff2ttf(w){var n=u16(w,12),dir=[],i;
  for(i=0;i<n;i++){var o=44+20*i;dir.push({tag:w.subarray(o,o+4),off:u32(w,o+4),cl:u32(w,o+8),ol:u32(w,o+12),ck:u32(w,o+16)})}
  return Promise.all(dir.map(function(d){var raw=w.subarray(d.off,d.off+d.cl);return d.cl<d.ol?strm(raw,new DecompressionStream('deflate')):Promise.resolve(raw)})).then(function(data){
    var len=12+16*n;data.forEach(function(t){len+=(t.length+3)&~3});
    var o=new Uint8Array(len),p=12+16*n,es=Math.floor(Math.log(n)/Math.LN2),sr=Math.pow(2,es)*16;
    function w32(a,v){o[a]=v>>>24&255;o[a+1]=v>>>16&255;o[a+2]=v>>>8&255;o[a+3]=v&255}
    function w16(a,v){o[a]=v>>8&255;o[a+1]=v&255}
    w32(0,u32(w,4));w16(4,n);w16(6,sr);w16(8,es);w16(10,n*16-sr);
    dir.forEach(function(d,k){var e=12+16*k;o.set(d.tag,e);w32(e+4,d.ck);w32(e+8,p);w32(e+12,data[k].length);o.set(data[k],p);p+=(data[k].length+3)&~3});
    return o})}
function parseTT(t,name){var n=u16(t,4),tb={},i,k;
  for(i=0;i<n;i++){var e=12+16*i;tb[String.fromCharCode(t[e],t[e+1],t[e+2],t[e+3])]=u32(t,e+8)}
  var hd=tb.head,hh=tb.hhea,upm=u16(t,hd+18),nh=u16(t,hh+34),adv=[],cm={},c=tb.cmap,best=-1,bf=0;
  for(i=0;i<nh;i++)adv.push(u16(t,tb.hmtx+4*i));
  for(i=0;i<u16(t,c+2);i++){var pid=u16(t,c+4+8*i),eid=u16(t,c+6+8*i),off=c+u32(t,c+8+8*i),f=u16(t,off);
    if(f===12&&(pid===3&&eid===10||pid===0)){best=off;bf=12}
    else if(f===4&&bf!==12&&(pid===3||pid===0)){best=off;bf=4}}
  if(best<0)throw new Error('cmap fehlt');
  if(bf===12){for(i=0;i<u32(t,best+12);i++){var g0=best+16+12*i,a=u32(t,g0),z=u32(t,g0+4),gid=u32(t,g0+8);for(k=a;k<=z;k++)cm[k]=gid+k-a}}
  else{var sx=u16(t,best+6),eo=best+14,so=eo+sx+2,dl=so+sx,ro=dl+sx;
    for(i=0;i<sx/2;i++){var en=u16(t,eo+2*i),st=u16(t,so+2*i),de=i16(t,dl+2*i),ra=u16(t,ro+2*i);
      for(k=st;k<=en&&k!==0xFFFF;k++){var g;if(!ra)g=(k+de)&65535;else{g=u16(t,ro+2*i+ra+2*(k-st));if(g)g=(g+de)&65535}if(g)cm[k]=g}}}
  var s=1000/upm;
  return {name:name,ttf:t,adv:adv,cm:cm,s:s,used:{},asc:Math.round(i16(t,hh+4)*s),desc:Math.round(i16(t,hh+6)*s),
    bbox:[i16(t,hd+36),i16(t,hd+38),i16(t,hd+40),i16(t,hd+42)].map(function(v){return Math.round(v*s)})}}
function gw(f,g){return (f.adv[g<f.adv.length?g:f.adv.length-1]||0)*f.s}
/* Text -> Glyphen; Zeichen, die in der Schrift fehlen, über REPL ersetzen, sonst "?" */
function glyphs(f,s,out,tief){s=String(s);out=out||[];for(var i=0;i<s.length;i++){var c=s.codePointAt(i);if(c>0xFFFF)i++;
  var ch=String.fromCodePoint(c);if(c===9||c===10)c=32;if(c<32||c===0xAD)continue;
  var g=f.cm[c];if(!g&&(c===0xA0||c===0x202F||c===0x2009||c===0x2007||c===0x2002||c===0x2003))g=f.cm[32];
  if(g){out.push(g);if(f.used[g]===undefined)f.used[g]=c;continue}
  if(REPL[ch]!==undefined&&!tief){glyphs(f,REPL[ch],out,1);continue}
  g=f.cm[63];if(g){out.push(g);f.used[g]=63}}return out}
/* lädt die Schrift fürs Zeichnen aus style#zeichen-schriften (nur wenn vorhanden und der Browser entpacken kann), sonst bleibt Helvetica */
function loadTT(){var st=document.getElementById('zeichen-schriften');TT=null;
  if(!st||!/Zeichenschrift/.test(st.textContent)||!window.DecompressionStream||!window.CompressionStream)return Promise.resolve(false);
  var css=st.textContent,get=function(w){var m=css.match(new RegExp('font-family:"Zeichenschrift";font-weight:'+w+';font-style:normal;[^}]*?base64,([A-Za-z0-9+/=]+)'));
    if(!m)return null;var b=atob(m[1]),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u};
  var r=get(400),bd=get(700);if(!r)return Promise.resolve(false);
  return Promise.all([woff2ttf(r),bd?woff2ttf(bd):null]).then(function(t){var f={r:parseTT(t[0],'Zeichenschrift')};f.b=t[1]?parseTT(t[1],'Zeichenschrift-Bold'):f.r;
    return Promise.all([strm(f.r.ttf,new CompressionStream('deflate')),f.b!==f.r?strm(f.b.ttf,new CompressionStream('deflate')):null]).then(function(z){
      f.r.z=z[0];if(f.b!==f.r)f.b.z=z[1];TT=f;return true})})}
function noTT(){TT=null}
function bin(u){var s='';for(var i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return s}
function hx(v){return ('0000'+v.toString(16)).slice(-4).toUpperCase()}
/* Objekte einer eingebetteten Schrift ab Nummer n: Type0 (Nummer fix), CIDFont n, FontDescriptor n+1, FontFile2 n+2, ToUnicode n+3 */
function ttObjs(f,fix,n,objs){var g=Object.keys(f.used).map(Number).sort(function(a,b){return a-b}),W='',U=[],i;
  g.forEach(function(x){W+=x+' ['+Math.round(gw(f,x))+'] '});
  g.forEach(function(x){var c=f.used[x],u=c>0xFFFF?String.fromCodePoint(c):String.fromCharCode(c),h='';for(i=0;i<u.length;i++)h+=hx(u.charCodeAt(i));U.push('<'+hx(x)+'> <'+h+'>')});
  var cm='/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n';
  for(i=0;i<U.length;i+=100){var part=U.slice(i,i+100);cm+=part.length+' beginbfchar\n'+part.join('\n')+'\nendbfchar\n'}
  cm+='endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend';
  objs[fix]='<< /Type /Font /Subtype /Type0 /BaseFont /'+f.name+' /Encoding /Identity-H /DescendantFonts ['+n+' 0 R] /ToUnicode '+(n+3)+' 0 R >>';
  objs[n]='<< /Type /Font /Subtype /CIDFontType2 /BaseFont /'+f.name+' /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor '+(n+1)+' 0 R /CIDToGIDMap /Identity /DW 500 /W ['+W+'] >>';
  objs[n+1]='<< /Type /FontDescriptor /FontName /'+f.name+' /Flags 32 /FontBBox ['+f.bbox.join(' ')+'] /ItalicAngle 0 /Ascent '+f.asc+' /Descent '+f.desc+' /CapHeight '+f.asc+' /StemV '+(f.name.indexOf('Bold')>0?120:80)+' /FontFile2 '+(n+2)+' 0 R >>';
  objs[n+2]='<< /Length '+f.z.length+' /Length1 '+f.ttf.length+' /Filter /FlateDecode >>\nstream\n'+bin(f.z)+'\nendstream';
  objs[n+3]='<< /Length '+cm.length+' >>\nstream\n'+cm+'\nendstream'}
/* Unicode-String -> String aus cp1252-Bytes (jedes Zeichen = 1 Byte) */
function toB(s){var o='';s=String(s);for(var i=0;i<s.length;i++){var ch=s[i],c=s.charCodeAt(i);
  if(c>=0xD800&&c<=0xDBFF){i++;o+='?';continue}
  if(REPL[ch]!==undefined){o+=REPL[ch];continue}
  if(c<32){o+=c===9||c===10?' ':'';continue}
  if(c<128||(c>=0xA0&&c<=0xFF)){o+=ch;continue}
  if(CP[c]!==undefined){o+=String.fromCharCode(CP[c]);continue}
  o+='?'}return o}
function esc(b){return b.replace(/\\/g,'\\\\').replace(/\(/g,'\\(').replace(/\)/g,'\\)')}
function num(n){return (Math.round(n*100)/100).toString()}
function rgb(c){c=c||[0,0,0];return num(c[0])+' '+num(c[1])+' '+num(c[2])}
function width(s,size,bold){if(TT){var f=bold?TT.b:TT.r,g=glyphs(f,s),q=0;for(var j=0;j<g.length;j++)q+=gw(f,g[j]);return q*size/1000/MM}var b=toB(s),W=bold?WB:WR,t=0;for(var i=0;i<b.length;i++)t+=W[b.charCodeAt(i)]||0;return t*size/1000/MM}
function hexUtf16(s){var h='FEFF';s=String(s);for(var i=0;i<s.length;i++){h+=('0000'+s.charCodeAt(i).toString(16)).slice(-4)}return '<'+h.toUpperCase()+'>'}

function Doc(opt){opt=opt||{};this.w=210;this.h=297;this.pages=[];this.info=opt.info||{};this.addPage()}
Doc.prototype.addPage=function(){this.cur=[];this.pages.push(this.cur);return this.pages.length};
Doc.prototype.text=function(s,x,y,size,bold,color){if(TT){var g=glyphs(bold?TT.b:TT.r,s);if(!g.length)return;
  this.cur.push('BT /'+(bold?'F2':'F1')+' '+num(size)+' Tf '+rgb(color)+' rg '+num(x*MM)+' '+num((this.h-y)*MM)+' Td <'+g.map(hx).join('')+'> Tj ET');return}
  s=toB(s);if(!s)return;
  this.cur.push('BT /'+(bold?'F2':'F1')+' '+num(size)+' Tf '+rgb(color)+' rg '+num(x*MM)+' '+num((this.h-y)*MM)+' Td ('+esc(s)+') Tj ET')};
Doc.prototype.line=function(x1,y1,x2,y2,lw,color){this.cur.push(rgb(color)+' RG '+num((lw||0.2)*MM)+' w 0 J '+num(x1*MM)+' '+num((this.h-y1)*MM)+' m '+num(x2*MM)+' '+num((this.h-y2)*MM)+' l S')};
Doc.prototype.rect=function(x,y,w,h,o){o=o||{};var op=o.fill&&o.stroke?'B':o.fill?'f':'S',s='';
  if(o.fill)s+=rgb(o.fill)+' rg ';if(o.stroke||!o.fill)s+=rgb(o.stroke)+' RG '+num((o.lw||0.2)*MM)+' w ';
  this.cur.push(s+num(x*MM)+' '+num((this.h-y-h)*MM)+' '+num(w*MM)+' '+num(h*MM)+' re '+op)};
Doc.prototype.poly=function(pts,lw,color){var H=this.h,s=rgb(color)+' RG '+num(lw*MM)+' w 1 J 1 j ';pts.forEach(function(p,i){s+=num(p[0]*MM)+' '+num((H-p[1])*MM)+(i?' l ':' m ')});this.cur.push(s+'S')};
Doc.prototype.build=function(){
  var self=this,objs=[],n=this.pages.length;
  var kids=[];for(var i=0;i<n;i++)kids.push((6+2*i)+' 0 R');
  objs[1]='<< /Type /Catalog /Pages 2 0 R >>';
  objs[2]='<< /Type /Pages /Kids ['+kids.join(' ')+'] /Count '+n+' >>';
  objs[3]='<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>';
  objs[4]='<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>';
  var inf=this.info,d=new Date(),p2=function(v){return ('0'+v).slice(-2)};
  var cd='D:'+d.getFullYear()+p2(d.getMonth()+1)+p2(d.getDate())+p2(d.getHours())+p2(d.getMinutes())+p2(d.getSeconds());
  objs[5]='<< /Title '+hexUtf16(inf.title||'')+' /Author '+hexUtf16(inf.author||'')+' /Subject '+hexUtf16(inf.subject||'')+' /Creator (KSV-Lernskript) /Producer (KSV-Lernskript) /CreationDate ('+cd+')'+(inf.ksv?' /KSV ('+inf.ksv+')':'')+' >>';
  this.pages.forEach(function(ops,i){var content=ops.join('\n');
    objs[6+2*i]='<< /Type /Page /Parent 2 0 R /MediaBox [0 0 '+num(self.w*MM)+' '+num(self.h*MM)+'] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents '+(7+2*i)+' 0 R >>';
    objs[7+2*i]='<< /Length '+content.length+' >>\nstream\n'+content+'\nendstream'});
  if(TT){ttObjs(TT.r,3,6+2*n,objs);if(TT.b!==TT.r)ttObjs(TT.b,4,10+2*n,objs);else objs[4]=objs[3]}
  var out='%PDF-1.4\n%\xE2\xE3\xCF\xD3\n',off=[];
  for(var k=1;k<objs.length;k++){off[k]=out.length;out+=k+' 0 obj\n'+objs[k]+'\nendobj\n'}
  var xr=out.length;out+='xref\n0 '+objs.length+'\n0000000000 65535 f \n';
  for(k=1;k<objs.length;k++)out+=('0000000000'+off[k]).slice(-10)+' 00000 n \n';
  out+='trailer\n<< /Size '+objs.length+' /Root 1 0 R /Info 5 0 R >>\nstartxref\n'+xr+'\n%%EOF';
  var u=new Uint8Array(out.length);for(var j=0;j<out.length;j++)u[j]=out.charCodeAt(j)&255;return u};

return {Doc:Doc,width:width,toB:toB,MM:MM,loadTT:loadTT,noTT:noTT};
})();
function sha256(ascii){function rr(v,a){return(v>>>a)|(v<<(32-a))}var mw=Math.pow(2,32),res='',w=[],bl=ascii.length*8,i,j,H=[],K=[],pc=0,comp={};
  for(var c=2;pc<64;c++){if(!comp[c]){for(i=0;i<313;i+=c)comp[i]=c;H[pc]=(Math.pow(c,.5)*mw)|0;K[pc++]=(Math.pow(c,1/3)*mw)|0}}
  ascii+='\x80';while(ascii.length%64-56)ascii+='\x00';
  for(i=0;i<ascii.length;i++){j=ascii.charCodeAt(i);if(j>>8)return '';w[i>>2]|=j<<((3-i)%4)*8}
  w[w.length]=((bl/mw)|0);w[w.length]=bl;
  for(j=0;j<w.length;){var ww=w.slice(j,j+=16),old=H;H=H.slice(0,8);
    for(i=0;i<64;i++){var w15=ww[i-15],w2=ww[i-2],a=H[0],e=H[4];
      var t1=H[7]+(rr(e,6)^rr(e,11)^rr(e,25))+((e&H[5])^((~e)&H[6]))+K[i]+(ww[i]=(i<16)?ww[i]:(ww[i-16]+(rr(w15,7)^rr(w15,18)^(w15>>>3))+ww[i-7]+(rr(w2,17)^rr(w2,19)^(w2>>>10)))|0);
      var t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&H[1])^(a&H[2])^(H[1]&H[2]));
      H=[(t1+t2)|0].concat(H);H[4]=(H[4]+t1)|0}
    for(i=0;i<8;i++)H[i]=(H[i]+old[i])|0}
  for(i=0;i<8;i++)for(j=3;j+1;j--){var b=(H[i]>>(j*8))&255;res+=((b<16)?0:'')+b.toString(16)}return res}
