1) Open your destination app / online banking.
2) Run copy_amount (bat/sh) then paste into Amount.
3) Run copy_reference (bat/sh) then paste Remark/Reference (keep WID).
4) Confirm transfer; keep provider receipt/txn id.
5) POST /admin/withdrawals/annotate-latest with that receipt.
6) POST /admin/universal/commit?wid=<wid> to mark PAID and (if not reserved) deduct vault.