<script lang="ts">
    /**
     * StatIcon.svelte
     * Purpose: Renders game-specific icons using the X-Wing Miniatures font.
     */

    type StatType =
        | "attack"
        | "agility"
        | "hull"
        | "shield"
        | "force"
        | "charge"
        | "calculate"
        | "focus"
        | "evade"
        | "lock"
        | "barrelroll"
        | "boost"
        | "coordinate"
        | "reinforce"
        | "jam"
        | "slam"
        | "reload"
        | "cloak"
        | "rotatearc"
        | "astromech"
        | "talent"
        | "missile"
        | "torpedo"
        | "cannon"
        | "turret"
        | "crew"
        | "gunner"
        | "device"
        | "illicit"
        | "modification"
        | "configuration"
        | "title"
        | "tech"
        | "recurring";
    let {
        type,
        size = "1em",
        color = "currentColor",
        className = "",
        style = "",
        isShip = false,
    }: {
        type: StatType | string;
        size?: string;
        color?: string;
        className?: string;
        style?: string;
        isShip?: boolean;
    } = $props();
    // Map of internal types to font characters based on xwing-miniatures.css
    const charMap: Record<string, string> = {
        attack: "%",
        agility: "^",
        hull: "&",
        shield: "*",
        force: "F",
        charge: "g",
        calculate: "a",
        focus: "f",
        evade: "e",
        lock: "l",
        barrelroll: "r",
        boost: "b",
        coordinate: "o",
        reinforce: "i",
        jam: "j",
        slam: "s",
        reload: "=",
        cloak: "k",
        rotatearc: "R",
        astromech: "A",
        missile: "M",
        torpedo: "P",
        cannon: "C",
        turret: "U",
        crew: "W",
        gunner: "Y",
        device: "B",
        illicit: "I",
        modification: "m",
        configuration: "n",
        title: "t",
        tech: "X",
        sensor: "S",
        recurring: "`",
        forcepower: "F",
        tacticalrelay: "Z",
        talent: "E",
        // Ship mappings (common ones, can be passing char as type too)
        t65xwing: "x",
        t70xwing: "w",
        btla4ywing: "y",
        rz1awing: "a",
        rz2awing: "E",
        asf01bwing: "b",
        tieadvancedx1: "A",
        tielnfighter: "F",
        tieinterceptor: "I",
        tiesabomber: "B",
        firesprayclasspatrolcraft: "f",
        yt1300lightfreighter: "m",
        modifiedyt1300lightfreighter: "m",
        scavengedyt1300: "Y",
        customizedyt1300lightfreighter: "W",
        vcx100lightfreighter: "G",
        fangfighter: "M",
        tieininterceptor: "I",
        belbullab22starfighter: "[",
        tieadvancedv1: "R",
        tiefofighter: "O",
        upsilonclassshuttle: "U",
        upsilonclasscommandshuttle: "U",
        sheathipedeclassshuttle: "%",
        attackshuttle: "g",
        arc170starfighter: "c",
        hwk290lightfreighter: "h",
        yt2400lightfreighter: "o",
        yv666lightfreighter: "t",
        vt49decimator: "d",
        lambdaclasst4ashuttle: "l",
        starviperclassattackplatform: "v",
        kihraxzfighter: "r",
        m3ainterceptor: "s",
        aggressorassaultfighter: "i",
        alphaclassstarwing: "&",
        auzituckgunship: "@",
        btlbywing: ":",
        btls8kwing: "k",
        droidtrifighter: "+",
        delta7aethersprite: "\\",
        escapecraft: "X",
        eta2actis: "-",
        ewing: "e",
        fireball: "0",
        g1astarfighter: "n",
        hmpdroidgunship: ".",
        hyenaclassdroidbomber: "=",
        jumpmaster5000: "p",
        laatigunship: "/",
        lancerclasspursuitcraft: "L",
        m12lkimogilafighter: "K",
        mg100starfortress: "Z",
        modifiedtielnfighter: "C",
        nabooroyaln1starfighter: "<",
        nantexclassstarfighter: ";",
        nimbusclassvwing: ",",
        quadrijettransferspacetug: "q",
        resistancetransport: ">",
        resistancetransportpod: "?",
        scurrgh6bomber: "H",
        sithinfiltrator: "]",
        syliureclasshyperspacering: "*",
        tieagaggressor: "`",
        tiebainterceptor: "j",
        tiecapunisher: "N",
        tieddefender: "D",
        tiephphantom: "P",
        tierbheavy: "J",
        tiereaper: "V",
        tiesffighter: "S",
        tieskstriker: "T",
        tievnsilencer: "$",
        ut60duwing: "u",
        v19torrentstarfighter: "^",
        vultureclassdroidfighter: "_",
        xiclasslightshuttle: "Q",
        tiewiwhispermodifiedinterceptor: "#",
        btanr2ywing: "{",
        clonez95headhunter: "}",
        rogueclassstarfighter: "|",
        st70assaultship: "'",
        gauntletfighter: "6",
        z95af4headhunter: "z",
    };
    const fontFamily = $derived(isShip ? "'XWingShip'" : "'XWing'");
    const iconChar = $derived((() => {
        const t = String(type);
        const normalized = t.toLowerCase().replace(/[^a-z0-9]/g, "");
        if (charMap[normalized]) return charMap[normalized];
        return t;
    })());

    const isError = $derived(iconChar.length > 1);
</script>

<span
    class="xwing-icon {className}"
    class:error-icon={isError}
    style="font-size: {size}; color: {isError ? '#ef4444' : color}; font-family: {isError ? 'inherit' : fontFamily}; {style}"
    aria-hidden="true"
>
    {isError ? '?' : iconChar}
</span>

<style>
    .xwing-icon {
        line-height: 1;
        display: inline-block;
        vertical-align: middle;
        font-weight: normal !important; /* Ensure no bolding */
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
</style>
