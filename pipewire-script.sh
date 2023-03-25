#!/bin/bash

#port.alias  /node.id /
#|| / PipeWire:Interface:Port/ || / PipeWire:Interface:Link/ || / PipeWire:Interface:Node/
#awk '/node.name/ || /node.nick/ || /node.description/ || /media.name/'
#awk '/node.id / || /port.name/ || /id: / || /id / || /direction: / || /port.alias/ || /node.name/ || /node.nick/ || /node.description/ || /media.name/'

if [[ $1 = "" ]] #print usage if no argumens are given
then
    echo "Usage:
 ./wipewire-script.sh save               - To save wires
 ./wipewire-script.sh load               - To load wires
 ./wipewire-script.sh getpid 'nodename'  - To get nodeid
 ./wipewire-script.sh getnid 'portname'  - To get portid
 ./wipewire-script.sh lsnodes            - To list all nodes with names
 ./wipewire-script.sh lsports            - To list all ports with names
 The config that is used for save and load is ./pipewirewires.conf"
    exit
fi

sortedpipewiretypes () {
    # ---------------------- Start Get PipeWire Links Nodes Ports ----------------------
    conlist=$(pw-cli ls | awk '/node.id / || /link./ || / type / || /port.direction/ || /port.alias/ || /node.name/ || /node.nick/ || /node.description/ || /media.name/ {for(i=1;i<=NF;i++){if((i!=2 || $2!="=") && $1!="id"){printf " %s", $i}}if($1=="id"){printf "%s",substr($4,20,length($4)-21) " \"" substr($2,1,length($2)-1) "\""}{print ""}}' | tac)
    # ---------------------- End Get PipeWire Links Nodes Ports ----------------------
    # ---------------------- Start Special List Sort ----------------------
    IFS=$'\n'
    nlist=""
    wlist=""
    for i in $conlist
    do
        if [[ ${i:0:1} == " " ]]
        then
            nlist=$nlist$i$'\n'
        else
            if [[ $i == *Port* || $i == *Link* || $i == *Node* ]]
            then
                nlist=$nlist$i$'\n'
                #echo "$nlist"
                wlist=$nlist$wlist
                nlist=""
            else
                nlist=""
            fi
        fi
    done
    echo "$wlist" #somewhat clean list that is still reversed but item order is not
    # ---------------------- End Special List Sort ----------------------
}

savewires () {
    # ---------------------- Start Save Wires ----------------------
    wlist=$1
    poli=$2
    noli=$3
    nlist=""
    fullil=""
    fullol=""
    for i in $wlist
    do
        if [[ ${i:0:1} == " " ]]
        then
            nlist=$nlist$i$'\n'
        else
            for j in $nlist
            do
                if [[ $j == *k.input.n* ]]
                then
                    inn=${j:17}
                elif [[ $j == *k.output.n* ]]
                then
                    oun=${j:18}
                elif [[ $j == *k.input.p* ]]
                then
                    inp=${j:17}
                elif [[ $j == *k.output.p* ]]
                then
                    oup=${j:18}
                fi
            done
            lili=$lili$'\n'$nlist
            jlist=""
            bli=""
            lateril=""
            laterol=""
            #echo "${i:5} $inn $oun $inp $oup"
            for g in $poli #Loop all ports to find the ports that are used by the link
            do
                if [[ ${g:0:1} == " " ]]
                then
                    jlist=$jlist" "$g$'\n'
                    bli=$bli$g$'\n'
                else
                    #jlist=$jlist$g
                    #echo to scan $jlist
                    for h in $jlist
                    do
                        if [[ ${h:0-${#inn}} == $inn && ${g:0-${#inp}} != $inp ]] #input node # && ${g:0-${#inp}} != $inp
                        then
                            #echo inputnode $jlist #> /dev/null
                            lateril=$lateril$jlist
                        elif [[ ${h:0-${#oun}} == $oun && ${g:0-${#oup}} != $oup ]] #output node # && ${g:0-${#oup}} != $oup
                        then
                            #echo outputnode $jlist #> /dev/null
                            laterol=$laterol$jlist
                        fi
                    done
                    if [[ ${g:0-${#inp}} == $inp ]] #input port
                    then
                        #echo inputport $jlist #> /dev/null
                        lateril=$bli$lateril
                    elif [[ ${g:0-${#oup}} == $oup ]] #output port
                    then
                        #echo outputport $jlist #> /dev/null
                        laterol=$bli$laterol
                    fi
                    jlist=""
                    bli=""
                fi
            done
            for g in $noli
            do
                if [[ ${g:0:1} == " " ]]
                then
                    jlist=$jlist${g:1}$'\n'
                else
                    #jlist=$jlist$g
                    if [[ ${g:0-${#inn}} == $inn ]]
                    then
                        #echo inputnodeinfo $jlist #> /dev/null
                        lateril=$jlist$'occorcence "1"\n'$lateril
                    elif [[ ${g:0-${#oun}} == $oun ]]
                    then
                        #echo outputnodeinfo $jlist #> /dev/null
                        laterol=$jlist$'occorcence "1"\n'$laterol
                    fi
                    jlist=""
                fi
            done
            fulll=$fulll$'\t\n'$lateril$laterol
            nlist=$nlist$i
            nlist=""
        fi
    done
    #echo "${fulll:2}" | awk '!/ node.id "/'
    echo "${fulll:2}" | awk '!/ node.id "/'
    # ---------------------- End Save Wires ----------------------
}

loadwires() {
    # ---------------------- Start Load Wires ----------------------
    conf=$1
    poli=$2
    noli=$3
    IFS=$'\t'
    for i in $conf #for all ports in config find the existig ports plus node and other ports to see if it is the same
    do
        #for i in $poli #for all ports find the relevant one in the config and get node plus other ports to see if it is correct
        cnodei=""
        cporti=""
        aextrai=""
        cnodeo=""
        cporto=""
        aextrao=""
        oc=1
        out=0
        IFS=$'\n'
        for g in $i $'\t'
        do
            if [[ ${g:0:2} == "  " ]]
            then
                if [[ $out == 0 ]]
                then
                    aextrai=$aextrai$'\n'${g:2}
                elif [[ $out == 1 ]]
                then
                    aextrao=$aextrao$'\n'${g:2}
                fi
            elif [[ ${g:0:1} == " " ]]
            then
                if [[ $out == 0 ]]
                then
                    cporti=$cporti$'\n'${g:1}
                elif [[ $out == 1 ]]
                then
                    cporto=$cporto$'\n'${g:1}
                fi
            elif [[ $g == $'\t' ]]
            then
                #PROSSES HERE FINAL AFTER READ
                #echo "$cnodei $cporti $aextrai $cnodeo $cporto $aextrao"
                # Find Port + Node + Extraports
                nlist=""
                IFS=$'\n'
                for j in $noli $'\t'
                do
                    if [[ ${j:0:1} == " " ]]
                    then
                        nlist=$nlist${j:1}$'\n'
                    elif [[ $j == $'\t' ]]
                    then
                        if [[ -n $oci && ${oci:0:1} != '"' ]] || [[ -n $oco && ${oci:0:1} != '"' ]]
                        then
                            echo skiping "$oci" "$oco" becalse it is incomplete
                        else
                            #HERE CONNECT
                            echo "pw-link ${oco:1:0-1} ${oci:1:0-1}"
                            pw-link "${oco:1:0-1}" "${oci:1:0-1}" #2>/dev/null
                        fi

                    else
                        #echo "$cnodei $cnodeo"
                        #echo "if"$'\n'"${nlist:0:0-1}-"$'\n'"${cnodei:1}-"
                        #echo $nlist
                        if [[ ${nlist:0:0-1} == ${cnodei:1} ]]
                        then
                            #echo "$nlist"
                            #echo ${j:5}
                            wlist=""
                            maid=""
                            iportcur=""
                            ipoextras=""
                            for h in $poli $'\t' #find ports that have the reqested node
                            do
                                if [[ ${h:0:1} == " " ]]
                                then
                                    if [[ ${h:1:8} == "node.id " ]]
                                    then
                                        maid=${h:9}
                                        #echo ${h:9}
                                    else
                                        wlist=$wlist${h:1}$'\n'
                                    fi
                                elif [[ $h == $'\t' ]]
                                then
                                    if [[ ${ipoextras:0:0-1} != ${aextrai:1} ]]  #if the remanig ports are not the same than the chosen port is incorect so skip it
                                    then
                                        iportcur=""
                                    fi
                                else
                                    if [[ $maid == ${j:5} ]]
                                    then
                                        #echo $maid == ${j:5}  --  $wlist
                                        if [[ ${wlist:0:0-1} == ${cporti:1} ]] #if port to use matches the one found save it
                                        then
                                            iportcur=${h:5}
                                        else #extraports
                                            ipoextras=$ipoextras$wlist
                                        fi
                                    fi
                                    #wlist=$wlist$h
                                    wlist=""
                                fi
                            done
                            if [[ $iportcur != "" ]]
                            then
                                if [[ $oci == "" ]]
                                then
                                    oci=-1
                                fi
                                if [[ $oci == -1 ]]
                                then
                                    oci="$iportcur"
                                elif [[ ${oci:0:1} != '"' && $oci -lt -1 ]]
                                then
                                    oci=$((oci+1))
                                fi
                            fi
                        elif [[ ${nlist:0:0-1} == ${cnodeo:1} ]]
                        then
                            #echo "$nlist"
                            #echo ${j:5}
                            wlist=""
                            maid=""
                            oportcur=""
                            opoextras=""
                            for h in $poli $'\t' #find ports that have the reqested node
                            do
                                if [[ ${h:0:1} == " " ]]
                                then
                                    if [[ ${h:1:8} == "node.id " ]]
                                    then
                                        maid=${h:9}
                                        #echo ${h:9}
                                    else
                                        wlist=$wlist${h:1}$'\n'
                                    fi
                                elif [[ $h == $'\t' ]]
                                then
                                    if [[ ${opoextras:0:0-1} != ${aextrao:1} ]]  #if the remanig ports are not the same than the chosen port is incorect so skip it
                                    then
                                        oportcur=""
                                    fi
                                else
                                    if [[ $maid == ${j:5} ]]
                                    then
                                        #echo $maid == ${j:5}  --  $wlist
                                        if [[ ${wlist:0:0-1} == ${cporto:1} ]] #if port to use matches the one found save it
                                        then
                                            oportcur=${h:5}
                                        else #extraports
                                            opoextras=$opoextras$wlist
                                        fi
                                    fi
                                    #wlist=$wlist$h
                                    wlist=""
                                fi
                            done
                            if [[ $oportcur != "" ]]
                            then
                                if [[ $oco == "" ]]
                                then
                                    oco=-1
                                fi
                                if [[ $oco == -1 ]]
                                then
                                    oco="$oportcur"
                                elif [[ ${oci:0:1} != '"' && $oco -lt -1 ]]
                                then
                                    oco=$((oco+1))
                                fi
                            fi
                        fi
                        nlist=$nlist$i
                        nlist=""
                    fi
                done
            else
                if [[ $out == 0 && $(echo $aextrai$cporti) != "" ]]
                then
                    out=1
                    oc=1
                elif [[ $out == 1 && $(echo $aextrao$cporto) != "" ]]
                then
                    echo Wrong config file.$'\n'More than one input and output per enrty can not be specified.$'\n'Tabs are use as seperator do not remove them.$'\n'Fix your active config file or save a new config to remove this error$'\n'Ignoring the entrys after the input and output entry row.
                    out=2
                fi
                if [[ ${g:0:11} == "occorcence " ]]
                then
                    oc=${g:11}
                elif [[ $out == 0 ]]
                then
                    oci=$((oc*-1))
                    cnodei=$cnodei$'\n'$g
                elif [[ $out == 1 ]]
                then
                    oco=$((oc*-1))
                    cnodeo=$cnodeo$'\n'$g
                fi
            fi

        done
    done
    # ---------------------- End Load Wires ----------------------
}

getidfromname () {
name=$1
options=$2
found=0
nlist=""
for i in $options
do
    if [[ ${i:0:1} == " " ]]
    then
        if [[ "$i" == *"\"$name\"" ]]
        then
            found=1
        fi
        #nlist=$nlist${i:1}$'\n'
    else
        #echo "$nlist$i"$'\n'
        if [[ $found == 1 ]]
        then
            echo ${i:6:0-1}
            found=0
        fi
        nlist=""
        #nlist=$nlist$i$'\n'
    fi

done
}

if [[ 1 == 1 ]] #always run get list and seperate it into links ports and nodes
then
    # ---------------------- Start Get Links + Ports + Nodes ----------------------

    wlist=$(sortedpipewiretypes)
    nlist=""
    noli=""
    poli=""
    lili=""
    IFS=$'\n'
    for i in $wlist
    do
        if [[ ${i:0:1} == " " ]]
        then
            nlist=$nlist$i$'\n'
        else
            if [[ $i == *Link* ]]
            then
                nlist=$nlist$i
                lili=$lili$'\n'$nlist
            elif [[ $i == *Port* ]]
            then
                nlist=$nlist$i
                poli=$poli$'\n'$nlist
            elif [[ $i == *Node* ]]
            then
                nlist=$nlist$i
                noli=$noli$'\n'$nlist
            fi
            nlist=""
        fi
    done
    # ---------------------- End Get Links + Ports + Nodes ----------------------
fi

if [[ $1 = "save" ]] #save
then
    savewires "$lili" "$poli" "$noli" > pipewirewires.conf # Save The Pipewire Wires
fi

if [[ $1 = "load" ]] #load
then
    conf=$(awk '{print $0}' pipewirewires.conf 2>/dev/null) #Read Config
    loadwires "$conf" "$poli" "$noli" #Load wires
fi

if [[ $1 = "getpid" ]] #get port id
then
    getidfromname "$2" "$poli"
fi

if [[ $1 = "getnid" ]] #get node id
then
    getidfromname "$2" "$noli"
fi

if [[ $1 = "lsnodes" ]] #list nodes
then
    for i in $noli
    do
        echo $i
        if [[ ${#i} -gt 0 && ${i:0:1} != " " ]]
        then
            echo ""
        fi
    done
fi

if [[ $1 = "lsports" ]] #list ports
then
    for i in $poli
    do
        echo $i
        if [[ ${#i} -gt 0 && ${i:0:1} != " " ]]
        then
            echo ""
        fi
    done
fi
