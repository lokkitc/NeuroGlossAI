import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../domain/entities/chat_session.dart';
import '../../domain/entities/chat_session_detail.dart';
import '../../domain/entities/chat_turn.dart';

class ChatSessionCache {
  static const _prefix = 'chat_session_cache_v1:';
  static const _defaultTtl = Duration(hours: 24);
  static const _maxTurns = 200;

  Future<ChatSessionDetailEntity?> load(String sessionId, {Duration ttl = _defaultTtl}) async {
    SharedPreferences sp;
    try {
      sp = await SharedPreferences.getInstance();
    } on PlatformException {
      return null;
    } catch (_) {
      return null;
    }

    final raw = sp.getString('$_prefix$sessionId');
    if (raw == null || raw.isEmpty) return null;

    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return null;
      final map = Map<String, dynamic>.from(decoded);

      final ts = map['ts'];
      final tsMs = ts is int ? ts : int.tryParse('$ts');
      if (tsMs != null) {
        final age = DateTime.now().difference(DateTime.fromMillisecondsSinceEpoch(tsMs));
        if (age > ttl) return null;
      }

      final data = map['data'];
      if (data is! Map) return null;
      return _detailFromJson(Map<String, dynamic>.from(data));
    } catch (_) {
      return null;
    }
  }

  Future<void> save(ChatSessionDetailEntity detail) async {
    SharedPreferences sp;
    try {
      sp = await SharedPreferences.getInstance();
    } on PlatformException {
      return;
    } catch (_) {
      return;
    }

    final trimmedTurns = detail.turns.length <= _maxTurns
        ? detail.turns
        : detail.turns.sublist(detail.turns.length - _maxTurns);

    final normalized = ChatSessionDetailEntity(session: detail.session, turns: trimmedTurns);

    final payload = {
      'ts': DateTime.now().millisecondsSinceEpoch,
      'data': _detailToJson(normalized),
    };

    try {
      await sp.setString('$_prefix${detail.session.id}', jsonEncode(payload));
    } on PlatformException {
      return;
    } catch (_) {
      return;
    }
  }

  Future<void> invalidate(String sessionId) async {
    SharedPreferences sp;
    try {
      sp = await SharedPreferences.getInstance();
    } on PlatformException {
      return;
    } catch (_) {
      return;
    }
    try {
      await sp.remove('$_prefix$sessionId');
    } on PlatformException {
      return;
    } catch (_) {
      return;
    }
  }

  Map<String, dynamic> _detailToJson(ChatSessionDetailEntity d) {
    return {
      'session': _sessionToJson(d.session),
      'turns': d.turns.map(_turnToJson).toList(growable: false),
    };
  }

  ChatSessionDetailEntity _detailFromJson(Map<String, dynamic> json) {
    final sess = _sessionFromJson(Map<String, dynamic>.from(json['session'] as Map));
    final turnsRaw = json['turns'];
    final turns = turnsRaw is List
        ? turnsRaw.map((e) => _turnFromJson(Map<String, dynamic>.from(e as Map))).toList(growable: false)
        : const <ChatTurnEntity>[];

    return ChatSessionDetailEntity(session: sess, turns: turns);
  }

  Map<String, dynamic> _sessionToJson(ChatSessionEntity s) {
    return {
      'id': s.id,
      'ownerUserId': s.ownerUserId,
      'title': s.title,
      'isArchived': s.isArchived,
      'characterId': s.characterId,
      'roomId': s.roomId,
      'enrollmentId': s.enrollmentId,
      'activeLevelTemplateId': s.activeLevelTemplateId,
    };
  }

  ChatSessionEntity _sessionFromJson(Map<String, dynamic> json) {
    return ChatSessionEntity(
      id: (json['id'] ?? '').toString(),
      ownerUserId: (json['ownerUserId'] ?? '').toString(),
      title: (json['title'] ?? '').toString(),
      isArchived: json['isArchived'] == true,
      characterId: json['characterId']?.toString(),
      roomId: json['roomId']?.toString(),
      enrollmentId: json['enrollmentId']?.toString(),
      activeLevelTemplateId: json['activeLevelTemplateId']?.toString(),
    );
  }

  Map<String, dynamic> _turnToJson(ChatTurnEntity t) {
    return {
      'id': t.id,
      'sessionId': t.sessionId,
      'turnIndex': t.turnIndex,
      'role': t.role,
      'content': t.content,
      'characterId': t.characterId,
      'meta': t.meta,
    };
  }

  ChatTurnEntity _turnFromJson(Map<String, dynamic> json) {
    final v = json['turnIndex'];
    final idx = v is int ? v : int.tryParse('$v') ?? 0;
    return ChatTurnEntity(
      id: (json['id'] ?? '').toString(),
      sessionId: (json['sessionId'] ?? '').toString(),
      turnIndex: idx,
      role: (json['role'] ?? '').toString(),
      content: (json['content'] ?? '').toString(),
      characterId: json['characterId']?.toString(),
      meta: (json['meta'] is Map) ? Map<String, dynamic>.from(json['meta'] as Map) : null,
    );
  }
}
