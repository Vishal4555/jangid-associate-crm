import { useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { Alert, Card, DataTable, EmptyState, PageHeader } from "../../components/ui";
import { getBillingDashboard } from "../../services/monthlyBillingService";
import type { BillingDashboard } from "../../types/monthlyBilling";

const currentMonth=()=>new Date().toISOString().slice(0,7);
const money=(value:string)=>new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR"}).format(Number(value));

export default function BillingDashboardPage(){
 const [month,setMonth]=useState(currentMonth()); const [data,setData]=useState<BillingDashboard|null>(null);
 const [loading,setLoading]=useState(false); const [error,setError]=useState("");
 useEffect(()=>{let active=true;setLoading(true);setError("");getBillingDashboard(month).then(x=>active&&setData(x)).catch(e=>active&&setError(e instanceof Error?e.message:"Unable to load dashboard")).finally(()=>active&&setLoading(false));return()=>{active=false}},[month]);
 const cards=data?[["Total Bank / Finance Billing",data.total_bank_billing],["Bank / Finance Received",data.bank_received],["Bank / Finance Outstanding",data.bank_outstanding],["Total Executive Payout",data.total_executive_payout],["Executive Paid",data.executive_paid],["Executive Outstanding",data.executive_outstanding],["Expected Gross Margin",data.expected_gross_margin],["Realized Cash Margin",data.realized_cash_margin]]:[];
 const monthControl=<label className="text-sm font-medium">Month<input type="month" value={month} onChange={e=>setMonth(e.target.value)} className="ml-2 border bg-white px-3 py-2 dark:bg-slate-900"/></label>;
 return <DashboardLayout><section className="space-y-4">
   <PageHeader eyebrow="Billing" title="Billing Dashboard" subtitle="Collections, payouts, and margin for the selected month." actions={monthControl}/>
   {loading&&<Card><p className="animate-pulse text-sm text-slate-500">Loading billing dashboard…</p></Card>}
   {error&&<Alert>{error}</Alert>}
   {data&&<><div className="flex items-center gap-3 text-sm"><span className="rounded-full bg-orange-100 px-3 py-1 font-semibold text-orange-800">{data.month_status.status}</span><span className="text-slate-500">Revision {data.month_status.revision_number}</span></div>
   <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label,value])=><Card key={label} className="flex min-h-24 flex-col justify-between"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-bold">{money(value)}</p></Card>)}</div>
   <Summary title="Bank / Finance Collection Summary" headers={["Bank / Finance Company","City","Billed","Received","Balance","Status"]} numericFrom={2} rows={data.bank_summary.map(x=>[x.bank,x.city||"—",money(x.billed_amount),money(x.received_amount),money(x.balance_amount),x.status])}/>
   <Summary title="Executive Payment Summary" headers={["Executive","Points","Gross","Advance","Net","Paid","Balance","Status"]} numericFrom={1} rows={data.executive_summary.map(x=>[x.executive,String(x.total_points),money(x.gross_payment||"0"),money(x.advance),money(x.net_payment||"0"),money(x.paid),money(x.balance||"0"),x.payment_status])}/></>}
 </section></DashboardLayout>
}

function Summary({title,headers,rows,numericFrom}:{title:string;headers:string[];rows:string[][];numericFrom:number}){return <section><h2 className="mb-2 text-lg font-bold">{title}</h2><DataTable><table className="min-w-[760px]"><thead><tr>{headers.map((x,index)=><th key={x} className={index>=numericFrom&&index<headers.length-1?"text-right":"text-left"}>{x}</th>)}</tr></thead><tbody>{rows.length?rows.map((row,i)=><tr key={i}>{row.map((x,j)=><td key={j} className={`${j>=numericFrom&&j<headers.length-1?"text-right ":""}whitespace-nowrap`}>{x}</td>)}</tr>):<tr><td colSpan={headers.length}><EmptyState>No billing data for this month.</EmptyState></td></tr>}</tbody></table></DataTable></section>}
