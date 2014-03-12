# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Block'
        db.create_table(u'db_block', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.IntegerField')()),
            ('prev_hash', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('merkle_root', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('bits', self.gf('django.db.models.fields.IntegerField')()),
            ('nonce', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('prev_block', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['db.Block'], null=True)),
        ))
        db.send_create_signal(u'db', ['Block'])


    def backwards(self, orm):
        # Deleting model 'Block'
        db.delete_table(u'db_block')


    models = {
        u'db.block': {
            'Meta': {'object_name': 'Block'},
            'bits': ('django.db.models.fields.IntegerField', [], {}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merkle_root': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'nonce': ('django.db.models.fields.IntegerField', [], {}),
            'prev_block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['db.Block']", 'null': 'True'}),
            'prev_hash': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['db']