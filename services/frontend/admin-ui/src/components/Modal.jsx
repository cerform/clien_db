import React from 'react'
export default function Modal({children,onClose}){
  return (
    <div className="modal" onClick={(e)=>{ if(e.target===e.currentTarget) onClose && onClose() }}>
      <div className="sheet">{children}</div>
    </div>
  )
}
