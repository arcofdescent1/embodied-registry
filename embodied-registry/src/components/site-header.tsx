import Link from "next/link";

export function SiteHeader() {
  return <header className="topbar public-header">
    <Link className="brand" href="/" aria-label="Embodied Registry home"><span className="brand-mark">ER</span><span>Embodied Registry</span><span className="alpha">ALPHA</span></Link>
    <nav aria-label="Primary navigation"><Link href="/">Registry</Link><Link href="/validator">Validator</Link><Link href="/thesis">Thesis</Link><Link href="/field-notes">Field notes</Link><Link href="/participate">Participate</Link></nav>
    <div className="top-actions"><Link className="primary-link" href="/validator">Install validator <span>↗</span></Link></div>
  </header>;
}
