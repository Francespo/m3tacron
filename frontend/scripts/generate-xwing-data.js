
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_ROOT = path.resolve(__dirname, '..');

function isDir(p) {
    try {
        return fs.existsSync(p) && fs.statSync(p).isDirectory();
    } catch {
        return false;
    }
}

function resolveExternalDataRoot() {
    const candidates = [
        path.join(FRONTEND_ROOT, 'external_data'),
        path.join(path.resolve(FRONTEND_ROOT, '..'), 'external_data'),
        '/external_data',
    ];

    for (const candidate of candidates) {
        if (isDir(path.join(candidate, 'xwing-data2')) || isDir(path.join(candidate, 'xwing-data2-legacy'))) {
            return candidate;
        }
    }

    return candidates[0];
}

const EXTERNAL_DATA_ROOT = resolveExternalDataRoot();
const FRONTEND_STATIC_ROOT = path.join(FRONTEND_ROOT, 'static');

console.log(`Resolved external data root: ${EXTERNAL_DATA_ROOT}`);
console.log(`Resolved frontend static root: ${FRONTEND_STATIC_ROOT}`);

const SOURCES = [
    {
        name: 'xwa',
        root: path.join(EXTERNAL_DATA_ROOT, 'xwing-data2'),
        output: path.join(FRONTEND_STATIC_ROOT, 'data-xwa', 'xwing-data.json')
    },
    {
        name: 'legacy',
        root: path.join(EXTERNAL_DATA_ROOT, 'xwing-data2-legacy'),
        output: path.join(FRONTEND_STATIC_ROOT, 'data-legacy', 'xwing-data.json')
    }
];

function loadJson(filePath) {
    if (!fs.existsSync(filePath)) {
        console.warn(`File not found: ${filePath}`);
        return null;
    }
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(content);
    } catch (e) {
        console.error(`Error reading ${filePath}:`, e);
        return null;
    }
}

function processSource(source) {
    console.log(`Processing ${source.name}...`);
    const manifestPath = path.join(source.root, 'data/manifest.json');
    const manifest = loadJson(manifestPath);

    if (!manifest) {
        console.error(`Manifest not found for ${source.name} at ${manifestPath}`);
        return;
    }

    const output = {
        ships: {},
        pilots: {},
        upgrades: {}
    };

    // 1. Process Pilots and Ships
    if (manifest.pilots) {
        manifest.pilots.forEach(factionEntry => {
            const faction = factionEntry.faction;
            factionEntry.ships.forEach(shipFileRelativePath => {
                // manifest paths are like "data/pilots/..."
                // actual files are in source.root + shipFileRelativePath
                // BUT "data/pilots" in manifest corresponds to "data/pilots" folder in root.
                
                const shipFilePath = path.join(source.root, shipFileRelativePath);
                const shipData = loadJson(shipFilePath);
                
                if (shipData) {
                    const shipXws = shipData.xws;
                    
                    // Store Ship Info
                    if (!output.ships[shipXws]) {
                        output.ships[shipXws] = {
                            name: shipData.name,
                            xws: shipData.xws,
                            size: shipData.size,
                            icon: shipData.icon,
                            stats: shipData.stats,
                            actions: shipData.actions,
                            factions: [faction] 
                        };
                    } else {
                        // Add faction if not exists
                        if (!output.ships[shipXws].factions.includes(faction)) {
                            output.ships[shipXws].factions.push(faction);
                        }
                    }

                    // Store Pilots
                    if (shipData.pilots) {
                        shipData.pilots.forEach(pilot => {
                            output.pilots[pilot.xws] = {
                                name: pilot.name,
                                xws: pilot.xws,
                                initiative: pilot.initiative,
                                limited: pilot.limited,
                                cost: pilot.cost,
                                loadout: pilot.loadout,
                                ship: shipXws,
                                faction: faction,
                                image: pilot.image,
                                artwork: pilot.artwork,
                                upgrades: pilot.upgrades, // Slots
                                caption: pilot.caption,
                                ability: pilot.ability,
                                shipAbility: pilot.shipAbility
                            };
                        });
                    }
                }
            });
        });
    }

    // 2. Process Upgrades
    if (manifest.upgrades) {
        manifest.upgrades.forEach(upgradeFileRelativePath => {
            const upgradeFilePath = path.join(source.root, upgradeFileRelativePath);
            const upgradeData = loadJson(upgradeFilePath);

            if (upgradeData) {
                // Upgrade files often contain multiple upgrades of the same Type
                if (Array.isArray(upgradeData)) {
                    upgradeData.forEach(upgrade => {
                         output.upgrades[upgrade.xws] = {
                            name: upgrade.name,
                            xws: upgrade.xws,
                            limited: upgrade.limited,
                            cost: upgrade.cost,
                            sides: upgrade.sides.map(side => ({
                                title: side.title,
                                type: side.type,
                                ability: side.ability,
                                slots: side.slots,
                                image: side.image,
                                artwork: side.artwork,
                                grants: side.grants
                            }))
                        };
                    });
                }
            }
        });
    }
    
    // Ensure output directory exists
    const outDir = path.dirname(source.output);
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }

    fs.writeFileSync(source.output, JSON.stringify(output, null, 2)); // formatted for debugging, can start minifying later
    console.log(`Written ${Object.keys(output.pilots).length} pilots, ${Object.keys(output.ships).length} ships, ${Object.keys(output.upgrades).length} upgrades to ${source.output}`);
}

SOURCES.forEach(source => processSource(source));
