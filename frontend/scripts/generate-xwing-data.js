
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
                    
                    const pilots = shipData.pilots || [];
                    const hasStandardPilots = pilots.some(p => p.standard === true || p.extended === true);

                    // Store Ship Info
                    if (!output.ships[shipXws]) {
                        output.ships[shipXws] = {
                            name: shipData.name,
                            xws: shipData.xws,
                            size: shipData.size,
                            icon: shipData.icon,
                            stats: shipData.stats,
                            actions: shipData.actions,
                            factions: [faction],
                            has_standard_pilots: hasStandardPilots,
                            epic: !hasStandardPilots
                        };
                    } else {
                        // Add faction if not exists
                        if (!output.ships[shipXws].factions.includes(faction)) {
                            output.ships[shipXws].factions.push(faction);
                        }
                        if (hasStandardPilots) {
                            output.ships[shipXws].has_standard_pilots = true;
                            output.ships[shipXws].epic = false;
                        }
                    }

                    // Store Pilots
                    if (shipData.pilots) {
                        shipData.pilots.forEach(pilot => {
                            const isStandardLegal = pilot.standard === true || pilot.extended === true;
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
                                shipAbility: pilot.shipAbility,
                                standard: pilot.standard ?? false,
                                extended: pilot.extended ?? false,
                                epic: pilot.epic ?? false,
                                valid_in_standard: isStandardLegal
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
                         const isStandardLegal = upgrade.standard === true || upgrade.extended === true;
                         output.upgrades[upgrade.xws] = {
                            name: upgrade.name,
                            xws: upgrade.xws,
                            limited: upgrade.limited,
                            cost: upgrade.cost,
                            standard: upgrade.standard ?? false,
                            extended: upgrade.extended ?? false,
                            epic: upgrade.epic ?? false,
                            valid_in_standard: isStandardLegal,
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
    
    // 3. Inject manual patches for missing scenario pilots
    const MANUAL_PILOTS = {
        // Evacuation of D'QAR
        "longshot-evacuationofdqar": { name: "Longshot", ship: "tiefofighter", faction: "firstorder" },
        "scorch-evacuationofdqar": { name: "Scorch", ship: "tiefofighter", faction: "firstorder" },
        "stomeronistarck-evacuationofdqar": { name: "Stomeroni Starck", ship: "t70xwing", faction: "resistance" },
        "zizitlo-evacuationofdqar": { name: "Zizi Tlo", ship: "rz2awing", faction: "resistance" },
        "caithrenalli-evacuationofdqar": { name: "C'ai Threnalli", ship: "t70xwing", faction: "resistance" },
        "ronithblario-evacuationofdqar": { name: "Ronith Blario", ship: "rz2awing", faction: "resistance" },
        "poedameron-evacuationofdqar": { name: "Poe Dameron", ship: "t70xwing", faction: "resistance" },
        "vennie-evacuationofdqar": { name: "Vennie", ship: "mg100starfortress", faction: "resistance" },
        "pettyofficerthanisson-evacuationofdqar": { name: "Petty Officer Thanisson", ship: "xiclasslightshuttle", faction: "firstorder" },
        "kyloren-evacuationofdqar": { name: "Kylo Ren", ship: "tievnsilencer", faction: "firstorder" },
        "midnight-evacuationofdqar": { name: "Midnight", ship: "tiefofighter", faction: "firstorder" },
        "zeta5-evacuationofdqar": { name: "Zeta 5", ship: "tiefofighter", faction: "firstorder" },
        "omega2-evacuationofdqar": { name: "Omega 2", ship: "tiefofighter", faction: "firstorder" },
        "theta3-evacuationofdqar": { name: "Theta 3", ship: "tiefofighter", faction: "firstorder" },
        "theta4-evacuationofdqar": { name: "Theta 4", ship: "tiefofighter", faction: "firstorder" },
        "jaycristubbs-evacuationofdqar": { name: "Jaycris Tubbs", ship: "t70xwing", faction: "resistance" },
        "pammichnerrogoode-evacuationofdqar": { name: "Pammich Nerro Goode", ship: "resistancetransport", faction: "resistance" },
        "lieutenantlehuse-evacuationofdqar": { name: "Lieutenant LeHuse", ship: "xiclasslightshuttle", faction: "firstorder" },
        "finchdallow-evacuationofdqar": { name: "Finch Dallow", ship: "mg100starfortress", faction: "resistance" },
        // Armed and Dangerous
        "fennrau-armedanddangerous": { name: "Fenn Rau", ship: "fangfighter", faction: "scumandvillainy" },
        "themandalorian-armedanddangerous": { name: "The Mandalorian", ship: "st70assaultship", faction: "scumandvillainy" },
        "dengar-armedanddangerous": { name: "Dengar", ship: "jumpmaster5000", faction: "scumandvillainy" },
        "bossk-armedanddangerous": { name: "Bossk", ship: "yv666lightfreighter", faction: "scumandvillainy" },
        "cadbane-armedanddangerous": { name: "Cad Bane", ship: "rogueclassstarfighter", faction: "scumandvillainy" },
        "princexizor-armedanddangerous": { name: "Prince Xizor", ship: "starviperclassattackplatform", faction: "scumandvillainy" },
        "bobafett-armedanddangerous": { name: "Boba Fett", ship: "firesprayclasspatrolcraft", faction: "scumandvillainy" },
        "zuckuss-armedanddangerous": { name: "Zuckuss", ship: "g1astarfighter", faction: "scumandvillainy" },
        "hansolo-armedanddangerous": { name: "Han Solo", ship: "customizedyt1300lightfreighter", faction: "scumandvillainy" },
        "fennecshand-armedanddangerous": { name: "Fennec Shand", ship: "modifiedtielnfighter", faction: "scumandvillainy" },
        "bokatankryze-armedanddangerous": { name: "Bo-Katan Kryze", ship: "gauntletfighter", faction: "scumandvillainy" }
    };

    Object.entries(MANUAL_PILOTS).forEach(([xws, patch]) => {
        if (!output.pilots[xws]) {
            output.pilots[xws] = {
                name: patch.name,
                xws: xws,
                initiative: 0,
                limited: 1,
                cost: 0,
                loadout: 0,
                ship: patch.ship,
                faction: patch.faction
            };
        }
    });

    // 4. Inject manual patches for missing scenario upgrades. These cards ship
    //    in scenario packs (Armed and Dangerous / Evacuation of D'QAR) and are
    //    absent from the vendored upstream data. The base XWS ids are injected
    //    so both the bare id and the "<id>-<pack>" variant resolve to a name.
    const MANUAL_UPGRADES = {
        // Evacuation of D'QAR
        "acceleratedsensorarray": { name: "Accelerated Sensor Array", slot: "Tech" },
        "dedicatedgunners": { name: "Dedicated Gunners", slot: "Gunner" },
        "determination": { name: "Determination", slot: "Talent" },
        "escortfighter": { name: "Escort Fighter", slot: "Talent" },
        "forthecause": { name: "For the Cause", slot: "Talent" },
        "precisionholotargeter": { name: "Precision Holotargeter", slot: "Tech" },
        "primedoverdrivethrusters": { name: "Primed Overdrive Thrusters", slot: "Tech" },
        "repulsorliftengines": { name: "Repulsorlift Engines", slot: "Modification" },
        "targetassistalgorithm": { name: "Target Assist Algorithm", slot: "Tech" },
        "threatsensors": { name: "Threat Sensors", slot: "Tech" },
        // Armed and Dangerous
        "adaptablepowersystems": { name: "Adaptable Power Systems", slot: "Modification" },
        "flechettecannons": { name: "Flechette Cannons", slot: "Cannon" },
        "homingbeacon": { name: "Homing Beacon", slot: "Sensor" },
        "kinesoswitch": { name: "Kineso Switch", slot: "Illicit" },
        "r2g8": { name: "R2-G8", slot: "Astromech" },
        "starboardthrusters": { name: "Starboard Thrusters", slot: "Modification" },
        "synchronizedhandling": { name: "Synchronized Handling", slot: "Tech" },
        "todo360": { name: "ToDo-360", slot: "Crew" },
        "fennecshand": { name: "Fennec Shand", slot: "Gunner" }
    };

    Object.entries(MANUAL_UPGRADES).forEach(([xws, patch]) => {
        if (!output.upgrades[xws]) {
            output.upgrades[xws] = {
                name: patch.name,
                xws: xws,
                limited: 0,
                cost: 0,
                sides: [{
                    title: patch.name,
                    type: patch.slot,
                    slots: [patch.slot]
                }]
            };
        }
    });

    // Ensure output directory exists
    const outDir = path.dirname(source.output);
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }

    fs.writeFileSync(source.output, JSON.stringify(output, null, 2)); // formatted for debugging, can start minifying later
    console.log(`Written ${Object.keys(output.pilots).length} pilots, ${Object.keys(output.ships).length} ships, ${Object.keys(output.upgrades).length} upgrades to ${source.output}`);
}

SOURCES.forEach(source => processSource(source));
