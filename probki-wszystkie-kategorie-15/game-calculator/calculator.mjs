// Pure price engine for a fictional configuration. No game/account/provider API.
export function calculate(catalog, request) {
  if (!catalog || typeof catalog !== 'object' || !Object.hasOwn(catalog, request.game)) throw new Error('Nieznana konfiguracja gry.');
  const game = catalog[request.game];
  if (!Array.isArray(game.levels) || !Array.isArray(game.step_minor) || game.levels.length < 2 || game.step_minor.length !== game.levels.length - 1 || new Set(game.levels).size !== game.levels.length || !game.step_minor.every(n => Number.isSafeInteger(n) && n > 0)) throw new Error('Nieprawidłowa tabela stawek.');
  const start = game.levels.indexOf(request.from), target = game.levels.indexOf(request.to);
  if (start < 0 || target < 0) throw new Error('Wybierz istniejące poziomy.');
  if (target <= start) throw new Error('Poziom docelowy musi być wyższy od początkowego.');
  if (typeof request.priority !== 'boolean' || typeof request.streaming !== 'boolean') throw new Error('Opcje muszą mieć wartość tak/nie.');
  if (!game.servers || !Object.hasOwn(game.servers,request.server) || !Number.isSafeInteger(game.servers[request.server].extra_minor) || game.servers[request.server].extra_minor<0) throw new Error('Wybierz istniejący serwer.');
  const steps = game.step_minor.slice(start,target);
  const server_extra_minor=game.servers[request.server].extra_minor;
  const base_minor = steps.reduce((sum,n)=>sum+n,0)+server_extra_minor;
  if (!Number.isSafeInteger(base_minor)) throw new Error('Kwota przekracza obsługiwany zakres.');
  const surcharge_percent = (request.priority ? 15 : 0) + (request.streaming ? 10 : 0);
  const surcharge_minor = Number((BigInt(base_minor)*BigInt(surcharge_percent)+50n)/100n);
  const total_minor = base_minor+surcharge_minor;
  if (!Number.isSafeInteger(total_minor)) throw new Error('Kwota przekracza obsługiwany zakres.');
  return {currency:'PLN',base_minor,server:request.server,server_extra_minor,surcharge_percent,surcharge_minor,total_minor,breakdown:steps.map((price_minor,i)=>({from:game.levels[start+i],to:game.levels[start+i+1],price_minor})),fixture_only:true};
}
