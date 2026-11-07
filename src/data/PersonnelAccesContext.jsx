import { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react'
import { useModules } from './ModulesContext.jsx'
import { personnelAPI, authAPI, getToken } from '../services/api.js'

const Context = createContext(null)
export function PersonnelAccesProvider({children}) {
  const {societe,aGRH,chargement:attenteSociete}=useModules()
  const [etat,setEtat]=useState({chargement:true,acces:null,user:null,erreur:'',version:0})
  const generation=useRef(0)
  const recharger=useCallback(async()=>{
    const n=++generation.current,token=getToken()
    setEtat(p=>({chargement:true,acces:null,user:null,erreur:'',version:p.version+1}))
    if (attenteSociete || !societe?.id || !aGRH) {
      setEtat(p=>({...p,chargement:false}));return
    }
    try {
      const [acces,user]=await Promise.all([personnelAPI.acces(),authAPI.me()])
      if (n===generation.current && token===getToken()) setEtat(p=>({...p,chargement:false,acces,user}))
    } catch(e) {
      if (n===generation.current && token===getToken()) setEtat(p=>({...p,chargement:false,erreur:e.message}))
    }
  },[societe?.id,aGRH,attenteSociete])
  useEffect(()=>{recharger();return()=>{generation.current++}},[recharger])
  return <Context.Provider value={{...etat,recharger}}>{children}</Context.Provider>
}
export function usePersonnelAcces(){return useContext(Context)}
// Lot 974 : la société a choisi la validation par une seule personne.
export function useValidationUnique(){return !!useContext(Context)?.acces?.validation_unique}
