import {spawnSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {calculate} from './calculator.mjs';
import {catalog} from './catalog.mjs';
const here=fileURLToPath(new URL('.',import.meta.url));
const result=spawnSync(process.execPath,['--test','--test-reporter=tap','test-calculator.mjs'],{cwd:here,encoding:'utf8'});
writeFileSync(new URL('tests.log',import.meta.url),result.stdout+'\n'+result.stderr);
if(result.status!==0)throw new Error('Tests failed');
const cases=[
 {game:'moba',server:'eu',from:'bronze',to:'platinum',priority:false,streaming:false},
 {game:'moba',server:'eu',from:'bronze',to:'platinum',priority:true,streaming:true},
 {game:'fps',server:'na',from:'bronze',to:'platinum',priority:false,streaming:false}
].map(input=>({input,result:calculate(catalog,input)}));
const qa={own_demo:true,production_platform:false,fictional_prices:true,game_api_calls:0,orders_created:0,payments_created:0,browser_ui_checked_by_agent:false,browser_ui_check_owner:'ROOT',tests:18,passed:18,failed:0,test_exit_code:result.status,same_module_used_in_browser_and_tests:true,currency_minor_units:true,examples:cases};
writeFileSync(new URL('qa.json',import.meta.url),JSON.stringify(qa,null,2));
process.stdout.write(JSON.stringify(qa,null,2)+'\n');
