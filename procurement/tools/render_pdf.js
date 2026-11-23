const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({viewport:{width:800,height:1130}});
  await pg.goto('file://' + require('path').resolve(process.argv[3]));
  await pg.pdf({path: process.argv[2], format:'A4', printBackground:true, preferCSSPageSize:true});
  
  await b.close();
})();
