"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { SegmentedControl } from "./ui/SegmentedControl";

export default function DataSourceToggle() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();
    const current = searchParams.get("source") || "xwa";

    const setSource = (source: string) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set("source", source);
        router.push(`${pathname}?${params.toString()}`, { scroll: false });
    };

    return (
        <SegmentedControl
            options={[{ label: "XWA", value: "xwa" }, { label: "Legacy", value: "legacy" }]}
            value={current}
            onChange={setSource}
        />
    );
}
