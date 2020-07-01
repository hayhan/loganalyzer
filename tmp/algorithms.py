 ### Format the table:
 1: IF match table title && in the table
 2:     IF NOT nested line && NOT empty line
 3:         This line is messed, delete
 4:     ELIF empty line && dsTableEntryProcessed && (NOT lastLineMessed)
 5:         reset some variables of processing status
 6:     ELIF NOT empty line
 7:         dsTableEntryProcessed <- True
 8:         IF tableMessed
 9:             re-construct the last element
10:         END 
11:         format the whole new log
12:     END
13: END

### Convert multi-line to one-line format
 1: FOR line IN newfile
 2:     save the timestamp for current line
 3:     remove the timestamp from current line
 4:     IF nested line
 5:         Concatenate current line to lastLine
 6:     ELSE it is primary line
 7:         it means concatenating ends
 8:         combine the timestamp and last content
 9:         write last line to norm file
10:         update last line parameters
11:             aka.
12:             lastLine <- current line
13:             lastLineTS <- currentLineTS
14:     END
15: END
16: update the final line of the file and write to norm file

### Extract label vector
 1: FOR log IN norm file
 2:     IF match the label pattern 'abn: '
 3:         write 'a' to the vector
 4:         remove the 'abn: ' from current log
 5:     ELSE
 6:         write '-' to the vector
 7:     END
 8: END
 9: write label vector and lineId to file
10: overwrite the old norm file with contents that labels are removed

 [Arxiv'18] Pinjia He, Jieming Zhu, Hongyu Zhang, Pengcheng Xu,
            Zibin Zheng, and Michael R. Lyu.
            A Directed Acyclic Graph Approach to Online Log Parsing, 2018.

https://github.com/logpai/logparser.git

### Tree search
 1: def treeSearch(self, rn, seq):
 2:     """
 3:     Browses the tree in order to find a matching cluster to a log
 4:     It does not generate new node
 5:     Attributes
 6:     ----------
 7:     rn     : Root node
 8:     seq    : Log sequence to test
 9:     return : The matching log cluster
10:     """
11:     retLogCluster = None
12:     seqLen = len(seq)
13:     if seqLen in rootnode.childD
14:         # Check if there is a key with the same length, namely
15:         # the cache mechanism. 
16:         #
17:         # Comment it out because cache mechanism may lead to
18:         # wrong classification of logs if two or more templates
19:         # are similar, in other words, the log may be accepted
20:         # by a template w/ matching similarity which is not the
21:         # highest.
22:         #
23:         # Paper: retLogCluster = self.keyTreeSearch(seq)
24:         ...

### Calculate the similarity
 1: # Calculate the similarity. The seq1 is template
 2: def SeqDist(self, seq1, seq2):
 3:     """
 4:     Calculate the simlilarity between the template and raw log
 5:     Attributes
 6:     ----------
 7:     seq1   : the template
 8:     seq2   : the raw log
 9:     return : retVal that represents the similarity
10:              updateTokenNum, the num of numOfPara (<*>) in current template
11:     """
12:     ...
13:     for token1, token2 in zip(seq1, seq2):
14:         if token1 == '<*>':
15:             numOfPara += 1
16:             # Comment out line below to count <*> in simTokens
17:             # Paper: continue
18:         if token1 == token2:
19:             simTokens += 1
20:         # Do not accept seq2 if some special tokens are different
21:         # between the template seq1 and current log seq2
22:         # This can prevent Drain from over-pasering some tokens
23:         for pn in self.para.rex_s_token:
24:             if (pn.fullmatch(token1) and pn.fullmatch(token2) and ...
25:                 (pn.fullmatch(token1) and pn.fullmatch(token2)==None) or \
26:                 (pn.fullmatch(token2) and pn.fullmatch(token1)==None):
27:                 sTokenNoMatch = 1
28:                 break
29:        if sTokenNoMatch:
30:             break

### Add cluster
 1: def addCluster(self, messageL, logIDList, clusterL, ...):
 2:     # The initial value of st is 0.5 times the percentage
 3:     # of non-digit tokens in the log message
 4:     numOfPara = 0
 5:     for token in messageL:
 6:         # In the pre-process of Drain domain, I replaced
 7:         # all possible digital var with <*> already
 8:         # Do not follow the original method in the paper
 9:         # section 4.1.2
10:         #
11:         # Paper: if self.hasNumbers(token):
12:         if token == '<*>':
13:             numOfPara += 1
14:     # The "st" is similarity threshold used by the similarity
15:     # layer, see paper formula (3)
16:     #
17:     # Paper: newCluster.st = 0.5 * (len(logmessageL)-numOfPara) / float(len(logmessageL))
18:     #
19:     # The initial st is the lower bound. Make it bigger to avoid over-parsing
20:     newCluster.st = 0.8
21:     newCluster.initst = newCluster.st

### Sliding window
 1: start_time <- time_data_vector[0]
 2: start_index <- 0
 3: end_index <- -1
 4: # Get the first start, end index, end time
 5: FOR cur_time IN time_data_vector
 6:     # Window end (end_time) selects the min if not equal
 7:     IF cur_time <= start_time + ['window_size']
 8:         end_index <- end_index+1
 9:     ELSE
10:         BREAK
11:     END
12: END
13: start_end_pair <- (start_index, end_index)
14: start_end_index_list <- append(start_end_pair)
15: # Move the start and end index until next sliding window
16: WHILE end_index < log_size - 1
17:     prev_win_start <- start_index
18:     FOR cur_time IN time_data_vector[prev_win_start:end]
19:         # Window start (start_time) selects the max if not equal
20:         IF cur_time < start_time + ['window_step_size']
21:             start_index <- start_index+1
22:         ELSE
23:             start_time <- cur_time
24:             BREAK
25:         END
26:     END
27:     end_index <- start_index - 1
28:     curr_win_start <- start_index
29:     FOR cur_time IN time_data[curr_win_start:end]
30:         # Window end (end_time) selects the min if not equal
31:         IF cur_time <= start_time + ['window_size']
32:             end_index <- end_index+1
33:         ELSE
34:             BREAK
35:         END
36:     END
37:     start_end_pair <- (start_index, end_index)
38:     start_end_index_list <- append(start_end_pair)

### Construct ECM
 1: labels <- []
 2: event_count_matrix[inst_number x feature_number] <- ZEROs
 3: FOR j IN [0: inst_number-1]
 4:     label <- 0   # 0 represents success, 1 represents failure
 5:     FOR k IN expanded_indexes_list[j]
 6:         # Label the instance even if current log might not be in train template lib
 7:         IF label_vector[k]
 8:             label <- 1
 9:         END
10:         # Current log EventId, aka. template id
11:         event_id <- event_mapping_data[k]
12:         # Convert EventId to ZERO based index in shuffed EventId list
13:         try:
14:             event_index <- event_id_shuffled.index(event_id)
15:         except:
16:             continue
17:         # Increase the feature/event/template count in event count matrix
18:         event_count_matrix[j, event_index] <- event_count_matrix[j, event_index] + 1
19:     END
20:     # One label per instance. Labeling the instance if one log within is labeled at least
21:     labels <- append(label)
22: END

### tf-idf
 1: tf_matrix <- ECM
 2: num_instance <- ECM rows num
 3: df_vector <- numpy.sum(X > 0, axis=0)
 4: idf_vector <- numpy.log(num_instance / (df_vector + 1e-8))
 5: tf_idf_matrix <- tf_matrix * numpy.tile(idf_vector, (num_instance, 1)) 
 6: new_ECM <- tf_idf_matrix

### post-Process
 1: anomaly_window_list <- []
 2: FOR i IN [0: instance_num-1]
 3:     IF test_y_pred[i]
 4:         start_index <- start_end_index_list[i][0]
 5:         end_index <- start_end_index_list[i][1]
 6:         anomaly_window_list <- append(tuple((start_index, end_index)))
 7:     END
 8: END
 9: norm_time_list <- timestamp vector in structured_file
10: anomaly_timestamp_list <- []
11: FOR i IN [0: len(anomaly_window_list)-1]
12:     x <- anomaly_window_list[i][0]
13:     y <- anomaly_window_list[i][1]
14:     anomaly_timestamp_list <- append(tuple((norm_time_list[x], norm_time_list[y])))
15: END

### Incremental Drain
 1: Load the templates from the template library
 2: # Recover the tree from templates in library
 3: FOR each template IN library
 4:     logCluL <- addCluster()
 5: END
 6: Load the raw log data
 7: # Update the template library
 8: FOR each log IN raw
 9:     search the tree
10:     IF NOT match one node in tree
11:         newCluster <- new 
12:         newCluster <- log
13:         logCluL <- addCluster()
14:     ELSE
15:         currentCluster <- log
16:         update template in cluster conditionaly
17:     END
18: END

### merge the duplicated templates    
 1: tmp_eventL <- []
 2: FOR logClust IN logClustL
 3:     # The row[0/1/2/3]: [template_id_old, template_id, template_str, occurrence]
 4:     tmp_unique <- True
 5:     FOR row IN tmp_eventL
 6:         IF template_id == row[1]
 7:             print("Warning: template is duplicated, merging.")
 8:             tmp_unique <- False
 9:             IF row[0] != row[1]
10:                 IF template_id == template_id_old
11:                     row[0] <- row[1]
12:                 END
13:             row[3] <- row[3] + occurrence
14:             BREAK
15:             END
16:         END
17:     END
18:     # Drop current template if it is duplicate
19:     IF tmp_unique
20:         tmp_eventL <- append([template_id_old, template_id, template_str, occurrence])
21:     END
22: END

### old temp id
 1: FOR logClust IN logClustL
 2:     template_str <- logClust.logTemplate
 3:     occurrence <- len(logClust.outcell.logIDL)
 4:     template_id <- hash(template_str)
 5:     template_id_old <- logClust.template_id_old
 6:     ...
 7: END

### Init STIDLE
 1: event_id_templates_ext <- extract the eventId list from Template library
 2: event_id_templates_ext <- Pad ZEROs
 3: event_id_shuffled <- shuffle (event_id_templates_ext)
 4: Save event_id_shuffled to disk

### update STIDLE case 1
 1: # Case 1):
 2: event_id_old_zero <- Find the ZERO values in EventIdOld
 3: idx_zero_STIDLE <- Aggregate all idx of ZERO in STIDLE to a new list
 4: idx_zero_STIDLE_shuffled <- shuffle(idx_zero_STIDLE)
 5: # Insert the new EventId to the STIDLE
 6: FOR idx, tid IN [0: len(event_id_old_zero)-1]
 7:     # Make sure no duplicates in the STIDLE
 8:     TRY:
 9:         event_id_shuffled.index(tid)
10:     EXCEPT:
11:         event_id_shuffled[idx_zero_STIDLE_shuffled[idx]] <- tid
12:     END
13: END

### update STIDLE case 2
 1: # Case 2):
 2: FOR tidOld, tidNew in template library
 3:     IF tidOld != '0' AND tidOld != tidNew
 4:         idxOld <- event_id_shuffled.index(tidOld)
 5:         event_id_shuffled[idxOld] <- tidNew
 6:     END
 7: END

 ### incremental idf
 1: df_vec <- from ECM
 2: df_vec_accm, num_instance_accm <- from saved file
 3: df_vec_accm <- df_vec_accm + df_vec
 4: num_instance_accm <- num_instance_accm + num_instance
 5: idf_vec <- log (num_instance_accm/df_vec_accm)
 6: file <- idf_vec
 7: file <- df_vec_accm, num_instance_accm

### extract parameters
 1: idx_list <- Traverse all <*> in logEventTemplateL
 2: FOR idx IN idx_list
 3:     param_list <- append(logContentL[idx])
 4: END


[20200421-12:10:43.143] 
CM> 
RNG-RSP UsChanId=49  Adj: tim=8912 power=-50  Stat=Continue 
[20200421-12:10:43.414] [00:00:27 01/01/1970] [CmDocsisCtlThread] ...
[ 1235]
RNG-RSP UsChanId=49  Adj: tim= power=-8  Stat=Continue

### adapt boardfarm cm logs
 1: lastline <- empty line w/o LF or CRLF
 2: lastlineTS <- '[19700101-00:00:00.000]'
 3: currlineTS <- '[19700101-00:00:00.000]'
 4: recovContxt <- False
 5: FOR line IN rawfile
 6:     matchTS <- normalTimestamp.match(line)
 7:     matchAbnTS <- abnormalTimestamp.match(line)
 8:     IF matchTS
 9:         currlineTS <- normalTimestamp
10:     ESIF matchAbnTS
11:         line <- Replace current line abnormal timestamp with last line normal one
12:     # Other kind of line headings except both normal and abnormal timestamp
13:     ELSE
14:         # Not match the normal timestamp, and it is a primary line
15:         IF line NOT empty AND NOT nestedLine.match(line)
16:             IF recovContxt
17:                 lastline <- Remove the LF or CRLF of last line
18:             END
19:         ELSE
20:             recovContxt <- False
21:         END
22:     END
23:     # Start the recover context
24:     IF matchTS OR matchAbnTS
25:         lineNoTS <- remove timestamp from current line
26:         # Match the timestamp and it is an empty line
27:         IF lineNoTS NOT empty
28:             recovContxt <- True
29:         ELSE
30:             recovContxt <- False
31:         END
32:     END
33:     newfile <- write(lastline)
34:     lastline <- line
35:     lastlineTS <- currlineTS
36: END
37: newfile <- write(lastline)

### deeplog exec dataloader
 1: step1_dict = {"SeqIdx": 1-D array, zero-based, sequence index in the logs
 2:               "EventSeq": 2-D array, 1st dim is sequences, 2nd is a window of events
 3:               "Target": 1-D array, [0, num_classes-1], class index
 4:               "Label": 1-D array, 0/1, target label for each sequence
 5:              }

 1: ...
 2: keys = list(step1_dict.keys())
 3: return {k: step1_dict[k][index] for k in keys}
 4: ...
 5: dataloader = framework.DataLoader(step1_dict, batch_size=...)

    SeqIdx  EventSeq           Target    Label
    ------------------------------------------
    0       [12 32 12 25 23]   18        0      mini-batch 0
    1       [32 12 25 23 18]   38        0
    ------------------------------------------
    2       [12 25 23 18 38]   20        0      mini-batch 1
    3       [25 23 18 38 20]   53        0
    ------------------------------------------
    ...
    ------------------------------------------
    96      [21 23 13 22 37]   22        0      mini-batch 48
    97      [23 13 22 37 22]   18        0
    ------------------------------------------
    98      [13 22 37 22 18]   25        0      mini-batch 49

### deeplog exec train
 1: model <- DeepLogExec()
 2: criterion <- CrossEntropyLoss() Loss func combining LogSofmax and NLLLoss
 3: optimizer <- Adam()
 4: batch_cnt <- len(train_data_loader)
 5: FOR epoch IN range(NUM_EPOCHS)
 6:     epoch_loss <- 0
 7:     FOR batch_in IN train_data_loader
 8:         # Forward pass
 9:         seq <- (batch_in['EventSeq'] convert to 3-D tensor)
10:         output <- model(seq)
11:         loss <- criterion(output, batch_in['Target'])
12:
13:         # Backward pass and optimize
14:         optimizer.zero_grad()
15:         loss.backward()
16:         epoch_loss <- epoch_loss + loss.item()
17:         optimizer.step()
18:     END
19:     epoch_loss <- epoch_loss / batch_cnt
20: END
