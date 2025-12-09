1) Open destination app / online banking.
2) Copy amount (use copy scripts if any) and paste into Amount.
3) Paste 'WID ...' into Remark/Reference.
4) Confirm, keep receipt/txn id.
5) POST /admin/withdrawals/attach2?wid=<wid> with {'ref':'...'}
6) POST /admin/universal/commit?wid=<wid> to mark PAID (deduct if not reserved).