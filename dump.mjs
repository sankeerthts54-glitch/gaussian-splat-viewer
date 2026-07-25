import pkg from '@mkkellogg/gaussian-splats-3d';
console.log('Default export keys:', Object.keys(pkg));
console.log('Has KSplatConverter?', !!pkg.KSplatConverter);
import * as all from '@mkkellogg/gaussian-splats-3d';
console.log('All export keys:', Object.keys(all));
console.log('Has all.KSplatConverter?', !!all.KSplatConverter);
