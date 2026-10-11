// These are teaching/demo estimates, not official tariffs or live market prices.
export const services = {
  auto: {name: 'Auto-rickshaw', unit: 'km', base: 35, rate: 18, min: 60},
  taxi: {name: 'Local taxi', unit: 'km', base: 70, rate: 25, min: 120},
  guide: {name: 'Local guide', unit: 'hours', base: 0, rate: 400, min: 400},
  meal: {name: 'Casual meal', unit: 'people', base: 0, rate: 220, min: 220},
  activity: {name: 'Local activity', unit: 'people', base: 0, rate: 450, min: 450},
  hotel: {name: 'Budget room', unit: 'nights', base: 0, rate: 1600, min: 1600}
};
export const cities = [
  {id: 'guwahati', name: 'Guwahati', state: 'Assam', lat: 26.1445, lon: 91.7362, factor: 1, areas: ['City centre', 'Station area', 'Temple approach', 'Riverfront']},
  {id: 'jaipur', name: 'Jaipur', state: 'Rajasthan', lat: 26.9124, lon: 75.7873, factor: 1.05, areas: ['City centre', 'Station area', 'Old city', 'Fort approach']},
  {id: 'delhi', name: 'Delhi', state: 'Delhi', lat: 28.6139, lon: 77.209, factor: 1.2, areas: ['City centre', 'Station area', 'Market area', 'Monument approach']},
  {id: 'agra', name: 'Agra', state: 'Uttar Pradesh', lat: 27.1767, lon: 78.0081, factor: 1, areas: ['City centre', 'Station area', 'Monument approach', 'Market area']},
  {id: 'varanasi', name: 'Varanasi', state: 'Uttar Pradesh', lat: 25.3176, lon: 82.9739, factor: .95, areas: ['City centre', 'Station area', 'Ghat approach', 'Market area']},
  {id: 'goa', name: 'Panaji / Goa', state: 'Goa', lat: 15.4909, lon: 73.8278, factor: 1.4, areas: ['City centre', 'Bus stand area', 'Beach approach', 'Market area']},
  {id: 'shillong', name: 'Shillong', state: 'Meghalaya', lat: 25.5788, lon: 91.8933, factor: 1.15, areas: ['City centre', 'Taxi stand area', 'Viewpoint approach', 'Market area']},
  {id: 'kolkata', name: 'Kolkata', state: 'West Bengal', lat: 22.5726, lon: 88.3639, factor: 1.1, areas: ['City centre', 'Station area', 'Market area', 'Riverfront']}
];
export const traps = [
  {id:'extras', name:'The price changes at the end', services:['auto','taxi','guide','activity'], type:'Hidden charges', text:'The starting quote may exclude parking, waiting or entry fees.', action:'Ask for the total and a written breakdown before starting.', area:1},
  {id:'detour', name:'The unscheduled shop stop', services:['auto','taxi','guide'], type:'Commission detour', text:'A service may redirect you to a shop instead of the agreed destination.', action:'Agree on the route and say no to stops you did not request.', area:2},
  {id:'menu', name:'No price shown before ordering', services:['meal'], type:'Price ambiguity', text:'An unpriced menu or a verbal special can make the final bill unclear.', action:'Confirm item prices, taxes and service charges before ordering.', area:3},
  {id:'deposit', name:'Urgent advance payment', services:['hotel','activity','guide'], type:'Payment pressure', text:'Pressure to pay before you can check what is included is a warning sign.', action:'Check the service details and receipt before paying.', area:2},
  {id:'closed', name:'Your destination is supposedly closed', services:['auto','taxi','guide'], type:'Destination diversion', text:'A claim that your destination is closed may be used to sell an alternative.', action:'Verify with the destination directly rather than accepting a substitute.', area:1},
  {id:'room', name:'The room rate excludes basics', services:['hotel'], type:'Hidden charges', text:'Taxes, occupancy, check-in time and facilities may change the total.', action:'Ask for the full stay total and cancellation terms in writing.', area:0}
];
// Synthetic traveller history is visible for demonstration, never counted as real reports.
export const seedFares = cities.flatMap(city => Object.keys(services).flatMap(service => [0.9,1,1.1].map((scale,i) => {
  const s=services[service]; const amount=(service==='auto'||service==='taxi')?5:1;
  return {id:`seed-${city.id}-${service}-${i}`,city:city.id,service,amount,fare:Math.round(Math.max(s.min,s.base+s.rate*amount)*city.factor*scale),source:'Illustrative sample'};
})));
export const demos = [
  {name:'A fair city ride',city:'guwahati',service:'auto',amount:5,quote:140,flags:[],area:'City centre'},
  {name:'A quote worth questioning',city:'jaipur',service:'taxi',amount:8,quote:420,flags:['extras'],area:'Station area'},
  {name:'Pressure + a huge markup',city:'goa',service:'guide',amount:2,quote:3500,flags:['pressure','diversion'],area:'Beach approach'}
];
